from ytmusicapi import YTMusic, OAuthCredentials
from .config import OATH_JSON, CLIENT_ID, CLIENT_SECRET

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


def create_ytmb_all_playlist(playlists):
    """Create ytmb-all playlist if it doesn't exist.

    Parameters
    ----------
    playlists : list
        List of playlists returned by get_all_playlists. The playlist titles are checked
        and the ytmb-all playlist is created if it doesn't exist.

    Returns
    -------
    str
        ID of playlist.
    """
    ytmb_all_title = "ytmb-all"

    playlist_titles = [p["title"] for p in playlists]

    if ytmb_all_title not in playlist_titles:
        playlist_id = ytmusic.create_playlist(
            title=ytmb_all_title,
            description="Playlist automatically created by YTMB",
        )
    else:
        for p in playlists:
            if p["title"] == ytmb_all_title:
                playlist_id = p["playlistId"]
                break

    return playlist_id
