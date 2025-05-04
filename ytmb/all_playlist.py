from ytmb.api_client import create_playlist


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
        playlist_id = create_playlist(
            title=ytmb_all_title,
            description="Playlist automatically created by YTMB",
        )
    else:
        playlist_id = next(
            (p["playlistId"] for p in playlists if p["title"] == ytmb_all_title), None
        )

    return playlist_id
