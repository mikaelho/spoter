# coding: utf-8

"""
Spotify Web API access lib for Python

Follows the OAuth2 flow as documented here:
    https://developer.spotify.com/documentation/general/guides/authorization-guide/
"""

from functools import wraps
import os
import os.path
import threading
import time
from urllib.parse import urlencode, urljoin, quote, unquote, urlparse, parse_qs, urlunparse
import webbrowser

import bottle
import requests


class Spoter:

    environ_client_id = 'SPOTIFY_CLIENT_ID'
    environ_client_secret = 'SPOTIFY_CLIENT_SECRET'
    auth_endpoint = 'https://accounts.spotify.com/authorize'
    redirect_uri = 'http://localhost:8090/oauth2callback'
    token_endpoint = f'https://accounts.spotify.com/api/token'
    base_url = 'https://api.spotify.com/v1'

    user_info_url = f'{base_url}/me'
    remove_from_playlist = f'{base_url}/playlists/{{playlist_id}}/tracks'

    def __init__(self,
                 client_id=None,
                 client_secret=None,
                 scope='user-library-read',
                 refresh_token_file='~/Documents/spotify_refresh_token',
                 quiet=True):
        self.quiet = quiet
        self.access_token = None

        client_id = client_id or os.environ.get(self.environ_client_id)
        client_secret = client_secret or os.environ.get(
            self.environ_client_secret)

        if not (client_id and client_secret):
            raise Exception(f'client_id and/or client_secret not provided - '
                            f'include as constructor parameters or set environment '
                            f'variables {self.environ_client_id} and '
                            f'{self.environ_client_secret}.'
                            )

        self.refresh_token_filename = os.path.expanduser(
            refresh_token_file + '_' + client_id)

        self.auth_params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': scope
        }
        self.auth_url = (f'{self.auth_endpoint}?{urlencode(self.auth_params)}')
        self.token_params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': self.redirect_uri,
            'scope': scope
        }

    def _get_access_token(self):
        if self.access_token is not None:
            return self.access_token
        try:
            with open(self.refresh_token_filename, 'r') as fp:
                refresh_token = fp.read()
            self._refresh(refresh_token)
            return self.access_token
        except FileNotFoundError:
            self._request_token()
            return self.access_token

    class _AuthServer(bottle.ServerAdapter):
        server = None

        def run(self, handler):
            from wsgiref.simple_server import make_server, WSGIRequestHandler
            if self.quiet:
                class QuietHandler(WSGIRequestHandler):
                    def log_request(*args, **kw): pass

                self.options['handler_class'] = QuietHandler
            self.server = make_server(
                self.host, self.port,
                handler, **self.options)
            self.server.serve_forever()

        def stop(self):
            self.server.shutdown()

    def _request_token(self):
        app = bottle.Bottle()

        @app.route('/oauth2callback')
        def index():
            code = bottle.request.query.code
            token_params = self.token_params.copy()
            token_params['code'] = code
            token_params['grant_type'] = 'authorization_code'
            success, result = self._actual_token_request(token_params)
            if success:
                return 'Authentication complete'
            else:
                return result

        server = Spoter._AuthServer(port=8090)

        threading.Thread(
            group=None,
            target=app.run,
            name=None, args=(),
            kwargs={'server': server, 'quiet': self.quiet}
        ).start()

        time.sleep(1)

        try:
            webbrowser.open_new(self.auth_url)
            while self.access_token is None:
                time.sleep(0.1)
        finally:
            server.stop()

    def _refresh(self, refresh_token):
        token_params = self.token_params.copy()
        token_params['refresh_token'] = refresh_token
        token_params['grant_type'] = 'refresh_token'
        success, result = self._actual_token_request(token_params)
        if success:
            return
        if result['error'] == 'invalid_grant':
            self.access_token = None
            os.remove(self.refresh_token_filename)
            raise FileNotFoundError('Need to log in again')
        raise Exception(f'Spotify Web API auth error - {result.text}')

    def _actual_token_request(self, token_params):
        req = requests.post(self.token_endpoint, data=token_params)
        result = req.json()
        if 'access_token' in result:
            self.access_token = result['access_token']
            if 'refresh_token' in result:
                with open(self.refresh_token_filename, 'w') as fp:
                    fp.write(result['refresh_token'])
            return (True, result)
        return (False, result)

    # docgen: Decorators

    def authenticated(func):
        """ Decorator """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            headers = kwargs.setdefault('headers', {})

            headers['Authorization'] = 'Bearer ' + self._get_access_token()
            result = func(self, *args, **kwargs)

            if result.status_code < 400:
                return result

            if result.status_code == 401:
                self.access_token = None
                headers['Authorization'] = 'Bearer ' + self._get_access_token()
                result = func(self, *args, **kwargs)
                if result.status_code < 400:
                    return result
            raise Exception(
                f'Error in making a Spotify Web API request', result.text)

        return wrapper

    def flexible_id(func):
        """ Decorator """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            item_id = args[0]
            try:
                item_id = args[0]['id']
            except (KeyError, TypeError): pass
            return func(self, item_id, *args[1:], **kwargs)

        return wrapper

    # docgen: Authenticated requests methods

    @authenticated
    def get(self, *args, **kwargs):
        return requests.get(*args, **kwargs)

    @authenticated
    def post(self, *args, **kwargs):
        return requests.post(*args, **kwargs)

    @authenticated
    def patch(self, *args, **kwargs):
        return requests.patch(*args, **kwargs)

    @authenticated
    def delete(self, *args, **kwargs):
        return requests.delete(*args, **kwargs)

    def expand(self, url, **params):
        url_parts = list(urlparse(url))
        query = dict(parse_qs(url_parts[4]))
        query.update(params)
        url_parts[4] = urlencode(query, doseq=True)
        return urlunparse(url_parts)

    def get_user_info(self):
        return self.get(f'{self.user_info_url}').json()

    def search(self, query_string, content_type, **kwargs):
        """ See https://developer.spotify.com/documentation/web-api/reference/search/search/ """
        url = f'{self.base_url}/search?q={quote(query_string)}&type={content_type}'
        url = self.expand(url, **kwargs)
        return self.get(url).json()

    def user_playlists(self, **kwargs):
        url = f'{self.base_url}/me/playlists'
        url = self.expand(url, **kwargs)
        return self.get(url).json()

    @flexible_id
    def playlist_tracks(self, playlist_id, **kwargs):
        url = f'{self.base_url}/playlists/{playlist_id}/tracks'
        url = self.expand(url, **kwargs)
        return self.get(url).json()

    @flexible_id
    def track(self, track_id):
        url = f'{self.base_url}/tracks/{track_id}'
        return self.get(url).json()

    @flexible_id
    def delete_tracks_from_playlist(self, playlist_id, track_ids):
        url = f'{self.base_url}/playlists/{playlist_id}/tracks'
        print(url)
        data = {
            "tracks": [ 
                { "uri": f'spotify:track:{track_id}' }
                for track_id in track_ids
            ]
        }
        print(data)
        return self.delete(url, data=data)


if __name__ == '__main__':

    from pprint import pprint

    client_id = None
    client_secret = None
    try:
        import spotify_ids

        client_id = spotify_ids.client_id
        client_secret = spotify_ids.client_secret
    except ModuleNotFoundError:
        pass  # Rely on environment variables

    spot = Spoter(client_id=client_id, client_secret=client_secret)

    print()
    print('Search for 5 first playlists for "Medieval ambient" music')
    print('---------------------------------------------------------')
    result = spot.search('Medieval ambient', 'playlist', market='FI', limit=5)
    for item in result['playlists']['items']:
        print(item['name'])
        
    print()
    print('Tracks for the last playlist in my playlists')
    print('--------------------------------------------')
    result = spot.user_playlists()
    playlist = result['items'][-1]
    tracks = spot.playlist_tracks(playlist, limit=5)
    for track in tracks['items']:
        print(track['track']['name'])

    
    '''
    from pprint import pprint
    pprint(result)
    '''
