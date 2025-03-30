from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from models import Base, Playlist
from config import DB_URI

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
