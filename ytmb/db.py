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
from api_client import get_album_year

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


def store_track_from_playlist(
    session, playlist_data, track_data, track_position_in_playlist
):
    # Check if track exists
    track = session.query(Track).filter_by(ytmusic_id=track_data["videoId"]).first()

    if not track:
        # Check if album exists
        if track_data["album"] is not None and track_data["album"]["id"] is not None:
            album_id = track_data["album"]["id"]
            album_name = track_data["album"]["name"]
            album_year = get_album_year(album_id)
            album = session.query(Album).filter_by(ytmusic_id=album_id).first()
        else:
            album_id = 0
            album_name = "No album"
            album_year = 0
            album = session.query(Album).filter_by(ytmusic_id=album_id).first()

        # Create new track
        track = Track(
            ytmusic_id=track_data["videoId"],
            name=track_data["title"],
            album_id=album_id,
        )
        session.add(track)

        # Create and add new album if it doesn't exist
        if not album:
            album = Album(
                ytmusic_id=album_id,
                name=album_name,
                year=album_year,
            )
            session.add(album)

        # Handle TrackArtist relationship
        for artist_data in track_data["artists"]:
            # Check if artist exists
            if artist_data["id"] is not None:
                artist_id = artist_data["id"]
                artist = session.query(Artist).filter_by(ytmusic_id=artist_id).first()
                if not artist:
                    # Create and add new artist
                    artist = Artist(ytmusic_id=artist_id, name=artist_data["name"])

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
    # Check if album exists in albums table
    if album_data["browseId"] is not None:
        album_id = album_data["browseId"]
        album_name = album_data["title"]
        album_year = get_album_year(album_id)
        album = session.query(Album).filter_by(ytmusic_id=album_id).first()
    else:
        album_id = 0
        album_name = "No album"
        album_year = 0
        album = session.query(Album).filter_by(ytmusic_id=album_id).first()

    # Create and add new album if it doesn't exist
    if not album:
        album = Album(ytmusic_id=album_id, name=album_name, year=album_year)
        session.add(album)
        session.commit()

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
