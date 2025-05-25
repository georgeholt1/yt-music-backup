from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from .models import (
    Base,
    Playlist,
    Track,
    Artist,
    TrackArtist,
    PlaylistTrack,
    Album,
)
from .config import DB_URI

engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)


def initialize_database():
    Base.metadata.create_all(engine)


def store_playlists(session, playlists_data):
    """Store playlist information in the database if it does not already exist.

    Iterates through a list of playlist data, checks if each playlist is already
    present in the database by querying for its YouTube Music ID, and adds to
    the database if it is not. Commits changes.

    Paramaters
    ----------
    session : sqlalchemy.orm.Session
    playlists_data : list of dict
        List containing playlist data, where each dictionary must include
        `playlistId` and `title` keys.

    Returns
    -------
    playlists : list of dict
        List of playlist data. Each entry is a dict with keys "name",
        "ytmusic_id" (playlistId) and "playlist_table_id" (id in playlist table
        of database).
    """
    playlists = []
    for playlist_data in playlists_data:
        playlist = (
            session.query(Playlist).filter_by(title=playlist_data["title"]).first()
        )

        if not playlist:
            playlist = Playlist(title=playlist_data["title"])
            session.add(playlist)
            session.commit()

        playlists.append(
            {
                "name": playlist_data["title"],
                "ytmusic_id": playlist_data["playlistId"],
                "playlist_table_id": playlist.id,
            }
        )

    return playlists


def store_artists_from_tracks(session, tracks):
    """Store unique artists from a list of tracks.

    Extracts artists from tracks and stores each unique artist in the database.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    tracks : list
        List containing tracks. For example, returned by
        api_client.get_playlist_tracks."""
    unique_artists = {artist["name"] for track in tracks for artist in track["artists"]}

    for artist in unique_artists:
        store_artist(session, artist)


def store_albums_from_tracks(session, tracks):
    """Store unique albums from a list of tracks.

    Extracts albums from tracks and stores each unique album in the database.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    tracks : list
        List containing tracks. For example, returned by
        api_client.get_playlist_tracks.
    """
    unique_albums = {
        track["album"]["name"] for track in tracks if track.get("album") is not None
    }

    for album in unique_albums:
        store_album(session, album)


def store_album(session, album_name, user_saved=False):
    """Store an album in the database if not already present.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    album_name : str or None
        Name of the album.
    user_saved : bool, optional
        Boolean label to use for the `user_saved` column of the `albums` table.
        Defaults to False.

    Returns
    -------
    Album
        The album object stored in the database.
    """
    album = session.query(Album).filter_by(name=album_name).first()

    if not album:
        album = Album(name=album_name, user_saved=user_saved)
        session.add(album)
    elif user_saved and not album.user_saved:
        album.user_saved = True
    elif not user_saved and album.user_saved:
        album.user_saved = False

    session.commit()

    return album


def store_album_from_track_data(session, track_data):
    """Store album information extracted from track data in the database.

    Extracts album information from track data and stores it using
    `store_album`.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    track_data : dict
        Dictionary containing track information, including `album` key.

    Returns
    -------
    Album
        The album object stored in the database.
    """
    if track_data["album"] is None:
        album_name = "No album"
    else:
        album_name = track_data["album"]["name"]
    album = store_album(session, album_name)

    return album


def store_album_from_album_data(session, album_data, user_saved=False):
    """Store album information extracted from album data in the database.

    Extracts album information from album data and stores it using
    `store_album`.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    album_data : dict
        Dictionary containing album information, must include `title` key.
    user_saved : bool, optional
        Boolean label to use for the `user_saved` column of the `albums` table.
        Defaults to False.

    Returns
    -------
    Album
        The album object stored in the database.
    """
    if album_data["title"] is None:
        album_name = "No album"
    else:
        album_name = album_data["title"]

    album = store_album(session, album_name, user_saved=user_saved)

    return album


def store_track_from_playlist(
    session, playlist_table_id, track_data, track_position_in_playlist
):
    """Store track and relationships from a playlist in the database.

    Checks and stores track and related artist/album information in the
    database, and handles PlaylistTrack relationships.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    playlist_table_id : int
        The unique integer ID of the playlist in the playlists tabls of the
        database.
    track_data : dict
        Dictionary containing track information, must include `videoId`,
        `title`, `album`, and `artists`.
    track_position_in_playlist : int
        Position of the track within the playlist.
    """
    # Check if track exists
    track = session.query(Track).filter_by(ytmusic_id=track_data["videoId"]).first()

    if not track:
        album = store_album_from_track_data(session, track_data)

        # Create new track
        track = Track(
            ytmusic_id=track_data["videoId"],
            name=track_data["title"],
            album_id=album.id,
        )
        session.add(track)

        # Handle artists
        for artist_data in track_data["artists"]:
            artist = store_artist(session, artist_data["name"])

            # Create TrackArtist relation if it doesn't exist
            if (
                not session.query(TrackArtist)
                .filter_by(artist_id=artist.id, track_id=track.id)
                .first()
            ):
                track_artist = TrackArtist(artist_id=artist.id, track_id=track.id)
                session.add(track_artist)

    # Handle PlaylistTrack relationship
    if (
        not session.query(PlaylistTrack)
        .filter_by(playlist_id=playlist_table_id, track_id=track.id)
        .first()
    ):
        playlist_track = PlaylistTrack(
            playlist_id=playlist_table_id,
            track_id=track.id,
            position=track_position_in_playlist,
        )
        session.add(playlist_track)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def store_user_saved_album(session, album_data):
    """Store user-saved album information in the database.

    Stores album and associated artists in the user's saved albums.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    album_data : dict
        Dictionary containing album information, including `browseId`, `title`,
        and `artists`.
    """
    store_album_from_album_data(session, album_data, user_saved=True)

    for artist_data in album_data["artists"]:
        store_artist(session, artist_data["name"])

    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def store_artist(session, artist_name, user_saved=False):
    """Store artist information in the database if not already present.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    artist_name : str
    user_saved : bool, optional
        Boolean label to use for the `user_saved` column of the `artists` table.
        Defaults to False.

    Returns
    -------
    Artist
        The artist object stored in the database.
    """
    artist = session.query(Artist).filter_by(name=artist_name).first()

    # Add the artist if necessary
    if not artist:
        artist = Artist(name=artist_name, user_saved=user_saved)
        session.add(artist)
    # Update the user_saved info if necessary
    elif user_saved and not artist.user_saved:
        artist.user_saved = True
    elif not user_saved and artist.user_saved:
        artist.user_saved = False

    session.commit()

    return artist


def store_artist_from_artist_data(session, artist_data, user_saved=False):
    """Store artist information in the database using artist data retrieved
    using ytmusic api.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    artist_data : dict
        Dictionary containing artist information, including `browseId` and
        `artist` keys.
    user_saved : bool, optional
        Boolean label to use for the `user_saved` column of the `artists` table.
        Defaults to False.

    Returns
    -------
    Artist
        The artist object stored in the database.
    """
    artist = store_artist(session, artist_data["artist"], user_saved=user_saved)

    return artist


def get_all_ytmusic_ids_in_tracks_table(session):
    """Return a list of all ytmusic_id values in the tracks table.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    """
    ytmusic_ids = session.query(Track.ytmusic_id).all()
    ytmusic_ids_list = [ytmusic_id for (ytmusic_id,) in ytmusic_ids]
    return ytmusic_ids_list


def get_all_playlist_titles(session):
    """Return a list of all the title values in the playlists table.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    """
    titles = session.query(Playlist.title).all()
    titles_list = [title for (title,) in titles]
    return titles_list


def get_all_artist_names(session):
    """Return a list of all the name values in the artists table.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    """
    names = session.query(Artist.name).all()
    names_list = [name for (name,) in names]
    return names_list


def get_ytmusic_ids_for_playlist(session, playlist_name):
    """Get ytmusic_id values of tracks in playlist.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    playlist_name : str

    Returns
    -------
    list
    """
    ytmusic_ids = (
        session.query(Track.ytmusic_id)
        .join(PlaylistTrack, Track.id == PlaylistTrack.track_id)
        .join(Playlist, Playlist.id == PlaylistTrack.playlist_id)
        .filter(Playlist.title == playlist_name)
        .all()
    )

    ytmusic_ids_list = [ytmusic_id for (ytmusic_id,) in ytmusic_ids]

    return ytmusic_ids_list


def identify_playlists_to_remove(session, library_playlists):
    """
    Compare a list of playlists to the list of playlists in the database and return the
    difference.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    library_playlists : list of dicts
        List of library dictionaries. Each dict should have "name" key.

    Returns
    -------
    set
        The set of playlists in the database that are not in `library_playlists`.
    """
    library_playlist_titles = {p["name"] for p in library_playlists}
    db_playlist_titles = set(get_all_playlist_titles(session))

    playlists_to_remove = db_playlist_titles - library_playlist_titles
    return playlists_to_remove


def remove_playlists(session, playlists_to_remove):
    """Remove playlists from the database.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    playlists_to_remove : list
        List of playlist titles to remove from the database.
    """
    for title in playlists_to_remove:
        playlist = session.query(Playlist).filter_by(title=title).first()
        if playlist:
            session.delete(playlist)
    session.commit()


def identify_artists_to_remove(session, library_artists):
    """Compare a list of artists to the list of artists in the database and return the
    difference.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    library_artists : list
        List of library artist names.

    Returns
    -------
    set
        The set of artists in the database that are not in `library_artists`.
    """
    db_artist_names = set(get_all_artist_names(session))
    artists_to_remove = db_artist_names - library_artists
    return artists_to_remove


def remove_artists(session, artists_to_remove):
    """Remove artists from the database.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    artists_to_remove : list
        List of artist names to remove from the database.
    """
    for artist in artists_to_remove:
        artist = session.query(Artist).filter_by(name=artist).first()
        if artist:
            session.delete(artist)
    session.commit()
