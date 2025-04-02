from ytmusicapi import YTMusic, OAuthCredentials
from config import OATH_JSON, CLIENT_ID, CLIENT_SECRET

ytmusic = YTMusic(
    OATH_JSON,
    oauth_credentials=OAuthCredentials(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    ),
)


def get_all_playlists():
    return ytmusic.get_library_playlists(limit=None)


def get_playlist_tracks(playlist_id):
    playlist = ytmusic.get_playlist(playlistId=playlist_id, limit=None)
    return playlist["tracks"]


def get_album_year(id):
    album = ytmusic.get_album(id)
    try:
        year = album["year"]
    except KeyError:
        year = 0
    return year


def get_all_albums():
    return ytmusic.get_library_albums(limit=None)


def get_all_artists():
    return ytmusic.get_library_artists(limit=None)


def get_all_subscriptions():
    return ytmusic.get_library_subscriptions(limit=None)
