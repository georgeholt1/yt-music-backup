from ytmb.api_client import create_playlist

YTMB_ALL_TITLE = "ytmb-all"


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
    playlist_titles = [p["title"] for p in playlists]

    if YTMB_ALL_TITLE not in playlist_titles:
        playlist_id = create_playlist(
            title=YTMB_ALL_TITLE,
            description="Playlist automatically created by YTMB",
        )
    else:
        playlist_id = next(
            (p["playlistId"] for p in playlists if p["title"] == YTMB_ALL_TITLE), None
        )

    return playlist_id
