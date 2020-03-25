# spoter - Spotify Web API library

## Usage example

    from spoter import Spoter
    
    spot = Spoter(client_id=client_id, client_secret=client_secret)
    # Or set values as environment variables:
    # - SPOTIFY_CLIENT_ID
    # - SPOTIFY_CLIENT_SECRET
    
    print('Search for playlists for Medieval ambient music')
    print('-----------------------------------------------')
    result = spot.search('Medieval ambient', 'playlist')
    for item in result['playlists']['items']:
        print(item['name'])
        