from ytmb.api_client import create_playlist, add_tracks_to_playlist
from ytmb.db import (
    get_all_ytmusic_ids_in_tracks_table,
    get_all_playlist_titles,
    get_ytmusic_ids_for_playlist,
)

YTMB_ALL_TITLE = "ytmb-all"


def _create_ytmb_all_playlist(playlists):
    """Create ytmb-all playlist if it doesn't exist.

    Parameters
    ----------
    playlists : list
        List of playlists dicts. Each dict must have "name" and "ytmusic_id" keys. The
        playlist titles are checked and the ytmb-all playlist is created if it doesn't
        exist.

    Returns
    -------
    str
        ID of playlist.
    """
    playlist_titles = [p["name"] for p in playlists]

    if YTMB_ALL_TITLE not in playlist_titles:
        playlist_id = create_playlist(
            title=YTMB_ALL_TITLE,
            description="Playlist automatically created by YTMB",
        )
    else:
        playlist_id = next(
            (p["ytmusic_id"] for p in playlists if p["name"] == YTMB_ALL_TITLE), None
        )

    return playlist_id


def _get_ytmb_all_track_diff(session):
    """Get list of tracks in database that are not in ytmb-all playlist.

    Parameters
    ----------
    session : sqlalchemy.orm.Session

    Returns
    -------
    list of ytmusic_ids
    """
    ytmusic_ids_in_database = get_all_ytmusic_ids_in_tracks_table(session)

    playlist_titles = get_all_playlist_titles(session)

    if YTMB_ALL_TITLE in playlist_titles:
        ytmb_all_track_ytmusic_ids = get_ytmusic_ids_for_playlist(
            session, YTMB_ALL_TITLE
        )
    else:
        ytmb_all_track_ytmusic_ids = []

    track_diff = set(ytmusic_ids_in_database) - set(ytmb_all_track_ytmusic_ids)

    return list(track_diff)


def handle_ytmb_all_playlist(playlists, session):
    """Handle creation and modification of ytmb-all playlist.

    - Creates ytmb-all playlist if it doesn't exist.
    - Adds tracks that are in database but not in ytmb-all playlist.

    Parameters
    ----------
    playlists : list
        List of playlist dicts.
    session : sqlalchemy.orm.Session
    """
    ytmb_all_playlist_id = _create_ytmb_all_playlist(playlists)
    tracks_to_add = _get_ytmb_all_track_diff(session)
    add_tracks_to_playlist(playlist_id=ytmb_all_playlist_id, tracks=tracks_to_add)
