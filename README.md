# spoter - Spotify Web API library

## Usage example

Here's a quick example of initializing the library and searching for specific string in playlists:

    from spoter import Spoter
    
    spot = Spoter(client_id=client_id, client_secret=client_secret)
    
    result = spot.search('Medieval ambient', 'playlist')
    for item in result:
        print(item['name'])

You application needs to have a client ID and a client secret. See the instructions [here](https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app) for registering the app and to get these. Do not forget to add this Redirect URI: http://localhost:8089/oauth2callback

You can also provide the client id and secret in the following environment variables:
* `SPOTIFY_CLIENT_ID`
* `SPOTIFY_CLIENT_SECRET`

On first run, a web browser is opened for you to enter your Spotify username and password. A refresh token is stored on disk, and on further runs user interaction is not needed for authentication.

The default location and file name for the refresh token file is '~/Documents/spotify_refresh_token' – you can change it with the optional `refresh_token_file` Spoter init parameter.

Default scope is `user-library-read`. You can provide a comma-separated list of additional scopes with the `scope` Spoter init parameter. See [here](https://developer.spotify.com/documentation/general/guides/scopes/) for the different Spotify authentication scopes.