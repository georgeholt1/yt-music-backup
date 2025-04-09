from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    Playlist,
    Track,
    Artist,
    TrackArtist,
    PlaylistTrack,
    Album,
    UserSavedAlbum,
    UserSavedArtist,
)
from config import DB_URI

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
    """
    for playlist_data in playlists_data:
        exists = (
            session.query(Playlist)
            .filter_by(ytmusic_id=playlist_data["playlistId"])
            .first()
        )

        if not exists:
            new_playlist = Playlist(
                ytmusic_id=playlist_data["playlistId"], title=playlist_data["title"]
            )
            session.add(new_playlist)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def store_artists_from_tracks(session, tracks):
    unique_artists = {
        (artist["name"], artist["id"] if artist["id"] is not None else 0)
        for track in tracks
        for artist in track["artists"]
    }

    artists = [{"name": name, "id": artist_id} for name, artist_id in unique_artists]

    for artist in artists:
        store_artist(session, artist["name"], artist["id"])


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
    # Get all unique albums in playlist
    albums = [track["album"] for track in tracks]
    albums = set(tuple(sorted(a.items())) for a in albums if a is not None)
    albums = list(dict(a) for a in albums)

    for album in albums:
        store_album(session, album["id"], album["name"])


def store_album(session, album_ytmusic_id, album_name):
    """Store an album in the database if not already present.

    Checks and stores an album by its YouTube Music ID and name.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    album_ytmusic_id : str or None
        YouTube Music ID for the album.
    album_name : str or None
        Name of the album.

    Returns
    -------
    Album
        The album object stored in the database.
    """
    if album_ytmusic_id is None or album_name is None:
        album_ytmusic_id = 0
        album_name = "No album"

    album = session.query(Album).filter_by(ytmusic_id=album_ytmusic_id).first()

    if not album:
        album = Album(ytmusic_id=album_ytmusic_id, name=album_name)
        session.add(album)
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
    if track_data["album"] is not None and track_data["album"]["id"] is not None:
        album_ytmusic_id = track_data["album"]["id"]
        album_name = track_data["album"]["name"]
    else:
        album_ytmusic_id = 0
        album_name = "No album"

    album = store_album(session, album_ytmusic_id, album_name)

    return album


def store_album_from_album_data(session, album_data):
    """Store album information extracted from album data in the database.

    Extracts album information from album data and stores it using
    `store_album`.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    album_data : dict
        Dictionary containing album information, must include `browseId` and
        `title` keys.

    Returns
    -------
    Album
        The album object stored in the database.
    """
    if album_data["browseId"] is not None:
        album_ytmusic_id = album_data["browseId"]
        album_name = album_data["title"]
    else:
        album_ytmusic_id = 0
        album_name = "No album"

    album = store_album(session, album_ytmusic_id, album_name)

    return album


def store_track_from_playlist(
    session, playlist_data, track_data, track_position_in_playlist
):
    """Store track and relationships from a playlist in the database.

    Checks and stores track and related artist/album information in the
    database, and handles PlaylistTrack relationships.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    playlist_data : dict
        Dictionary containing playlist information, must include `playlistId`
        key.
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
            artist = store_artist(session, artist_data["name"], artist_data["id"])

            # Create TrackArtist relation if it doesn't exist
            if (
                not session.query(TrackArtist)
                .filter_by(artist_id=artist.id, track_id=track_data["videoId"])
                .first()
            ):
                track_artist = TrackArtist(
                    artist_id=artist.id, track_id=track_data["videoId"]
                )
                session.add(track_artist)

    # Handle PlaylistTrack relationship
    if (
        not session.query(PlaylistTrack)
        .filter_by(
            playlist_id=playlist_data["playlistId"], track_id=track_data["videoId"]
        )
        .first()
    ):
        playlist_track = PlaylistTrack(
            playlist_id=playlist_data["playlistId"],
            track_id=track_data["videoId"],
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
    album = store_album_from_album_data(session, album_data)

    album_id = album.id

    # Check if album exists in user_saved_albums table
    album = session.query(UserSavedAlbum).filter_by(album_id=album_id).first()

    # Create and add new album if it doesn't exist
    if not album:
        album = UserSavedAlbum(
            album_id=album_id,
        )
        session.add(album)

    # Add artists if necessary
    for artist_data in album_data["artists"]:
        if artist_data["id"] is not None:
            artist_id = artist_data["id"]
            artist = session.query(Artist).filter_by(ytmusic_id=artist_id).first()
            if not artist:
                # Create and add new artist
                artist = Artist(ytmusic_id=artist_id, name=artist_data["name"])
                session.add(artist)

        else:
            artist_id = 0
            artist = session.query(Artist).filter_by(name=artist_data["name"]).first()
            if not artist:
                artist = Artist(ytmusic_id=artist_id, name=artist_data["name"])
                session.add(artist)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def store_artist(session, artist_name, artist_id):
    """Store artist information in the database if not already present.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    artist_name : str
    artist_id : str
        YTMusic artist id.

    Returns
    -------
    Artist
        The artist object stored in the database.
    """
    if artist_id is not None and artist_id != 0:
        artist = session.query(Artist).filter_by(ytmusic_id=artist_id).first()

    else:
        artist_id = 0
        artist = session.query(Artist).filter_by(name=artist_name).first()

    if not artist:
        artist = Artist(ytmusic_id=artist_id, name=artist_name)
        session.add(artist)

    session.commit()

    return artist


def store_artist_from_artist_data(session, artist_data):
    """Store artist information in the database using artist data retrieved
    using ytmusic api.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    artist_data : dict
        Dictionary containing artist information, including `browseId` and
        `artist` keys.

    Returns
    -------
    Artist
        The artist object stored in the database.
    """
    artist = store_artist(session, artist_data["artist"], artist_data["browseId"])

    return artist


def store_subscribed_artist(session, artist_data):
    """Store subscribed artist information in the database.

    Stores artist information using `store_artist` and links to the user's
    subscribed artists.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    artist_data : dict
        Dictionary containing artist information, including `browseId` and
        `artist` keys.
    """
    artist = store_artist_from_artist_data(session, artist_data)

    artist_id = artist.id

    artist = session.query(UserSavedArtist).filter_by(artist_id=artist_id).first()

    if not artist:
        artist = UserSavedArtist(artist_id=artist_id)
        session.add(artist)

    session.commit()
