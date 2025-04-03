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
from api_client import get_playlist_tracks

engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)


def initialize_database():
    Base.metadata.create_all(engine)


def store_playlists(session, playlists_data):
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


def store_albums_from_playlist(session, playlist):
    # Get all unique albums in playlist
    tracks = get_playlist_tracks(playlist["playlistId"])
    albums = [track["album"] for track in tracks]
    albums = set(tuple(sorted(a.items())) for a in albums if a is not None)
    albums = list(dict(a) for a in albums)

    for album in albums:
        store_album(session, album["id"], album["name"])


def store_album(session, album_ytmusic_id, album_name):
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
    if track_data["album"] is not None and track_data["album"]["id"] is not None:
        album_ytmusic_id = track_data["album"]["id"]
        album_name = track_data["album"]["name"]
    else:
        album_ytmusic_id = 0
        album_name = "No album"

    album = store_album(session, album_ytmusic_id, album_name)

    return album


def store_album_from_album_data(session, album_data):
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

        # Handle TrackArtist relationship
        for artist_data in track_data["artists"]:
            if artist_data["id"] is not None:
                artist_id = artist_data["id"]
                artist = session.query(Artist).filter_by(ytmusic_id=artist_id).first()
                if not artist:
                    # Create and add new artist
                    artist = Artist(ytmusic_id=artist_id, name=artist_data["name"])
                    session.add(artist)

            else:
                artist_id = 0
                artist = (
                    session.query(Artist).filter_by(name=artist_data["name"]).first()
                )
                if not artist:
                    artist = Artist(ytmusic_id=artist_id, name=artist_data["name"])
                    session.add(artist)

            # session.flush()  # Generate ID

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


def store_artist(session, artist_data):
    if artist_data["browseId"] is not None:
        artist_id = artist_data["browseId"]
        artist = session.query(Artist).filter_by(ytmusic_id=artist_id).first()

    else:
        artist_id = 0
        artist = session.query(Artist).filter_by(name=artist_data["artist"]).first()

    if not artist:
        artist = Artist(ytmusic_id=artist_id, name=artist_data["artist"])
        session.add(artist)

    session.commit()

    return artist


def store_subscribed_artist(session, artist_data):
    artist = store_artist(session, artist_data)

    artist_id = artist.id

    artist = session.query(UserSavedArtist).filter_by(artist_id=artist_id).first()

    if not artist:
        artist = UserSavedArtist(artist_id=artist_id)
        session.add(artist)

    session.commit()
