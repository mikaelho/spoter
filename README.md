# spoter - Spotify Web API library

## Usage example

Here's a quick example of initializing the library and searching for specific string in playlists:

    from spoter import Spoter
    
    spot = Spoter(client_id=client_id, client_secret=client_secret)
    
    result = spot.search('Medieval ambient', 'playlist')
    for item in result:
        print(item['name'])

You application needs to have a client ID and a client secret. See the instructions [here](https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app) for registering the app and to get these. Also add this Redirect URI: http://localhost:8090/oauth2callback

As an alternative to the init parameters in the example above, you can also provide the client id and secret in the following environment variables:
* `SPOTIFY_CLIENT_ID`
* `SPOTIFY_CLIENT_SECRET`

On first run, a web browser is opened for you to enter your Spotify username and password. A refresh token is stored on disk, and on further runs user interaction is not needed for authentication.

The default location and file name for the refresh token file is '~/Documents/spotify_refresh_token' – you can change it with the optional `refresh_token_file` Spoter init parameter.

Default scopes are `playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private`. You can provide a space-separated list of scopes with the `scope` Spoter init parameter. See [here](https://developer.spotify.com/documentation/general/guides/scopes/) for the different Spotify authentication scopes.

## Note on IDs

Most methods have an ID as their first argument. This can be given as a plain ID (e.g. "6FLwmdmW77N1Pxb1aWsZmO") or a `dict` with the key `id` providing the actual ID. This is a convenience feature reflecting the fact that all Spotify items returned by the Web API have their ID included, and you do not need to separately dig it our every time you want to use the ID in the next query, as in the following example:

    first_playlist = spot.user_playlists()['items'][0]
    tracks = spot.playlist_tracks(first_playlist)


## Spoter methods

#### Get user information

    get_user_info()
    
Retrieve current user information ([Spotify documentation](https://developer.spotify.com/documentation/web-api/reference/users-profile/get-current-users-profile/)).

#### Search for content

    search(query_string, content_type, market=None, limit=None, offset=None, include_external=None)

Search different types of content in Spotify ([Spotify documentation](https://developer.spotify.com/documentation/web-api/reference/search/search/)).

See [here](https://support.spotify.com/us/using_spotify/features/search/) for the advanced keywords that can be used in the search query.

Valid values for `content_type` are: album, artist, playlist, track, show and episode. You can provide a comma-separated list of several types.

#### Get user's playlists

    user_playlists(limit=None, offset=None)
    
See [Spotify documentation](https://developer.spotify.com/documentation/web-api/reference/playlists/get-a-list-of-current-users-playlists/). All of the playlist [scopes](https://developer.spotify.com/documentation/general/guides/scopes/#overview) are needed to reliably receive all playlists.

#### Get tracks in a playlist

    playlist_tracks(playlist_id, fields=None, limit=None, offset=None, market=None, additional_types=None)

See [Spotify documentation](https://developer.spotify.com/documentation/web-api/reference/playlists/get-playlists-tracks/).

#### Delete tracks from a playlist

    delete_tracks_from_playlist(playlist_id, track_ids)
    
Delete either a single track or a list of tracks by ID from the given playlist.

See [Spotify documentation](https://developer.spotify.com/documentation/web-api/reference/playlists/remove-tracks-playlist/).

#### Retrieve all pages of a long list

    get_all(key_path, func, *args, **kwargs)

Retrieves all pages of a longer result.

Parameters:
* `key_path` - Lists of results are nested deeper in the result JSON. This parameter must contain the
  pediod-separated key path to the result list. For example, key path of "tracks.items" is equivalent
  to you locating the actual list in a single result with `result['tracks']['items']`.
* `func, *args, **kwargs` - Function to be repeatedly called including its regular parameters. You can
  include `limit` and `offset` to control the "chunk size" and starting point of the result retrieval.