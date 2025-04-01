from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ytmusic_id = Column(String, nullable=False)
    name = Column(String, nullable=False)

    tracks = relationship("TrackArtist", back_populates="artist")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ytmusic_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)

    artists = relationship("TrackArtist", back_populates="track")
    playlist_tracks = relationship("PlaylistTrack", back_populates="track")


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ytmusic_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    year = Column(Integer)

    tracks = relationship("Track", backref="album")


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ytmusic_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)

    playlist_tracks = relationship("PlaylistTrack", back_populates="playlist")


class TrackArtist(Base):
    __tablename__ = "track_artists"
    __table_args__ = (UniqueConstraint("artist_id", "track_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)

    artist = relationship("Artist", back_populates="tracks")
    track = relationship("Track", back_populates="artists")


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    __table_args__ = (UniqueConstraint("playlist_id", "track_id", "position"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    position = Column(Integer, nullable=False)

    playlist = relationship("Playlist", back_populates="playlist_tracks")
    track = relationship("Track", back_populates="playlist_tracks")


class UserSavedArtist(Base):
    __tablename__ = "user_saved_artists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)


class UserSavedAlbum(Base):
    __tablename__ = "user_saved_albums"

    id = Column(Integer, primary_key=True, autoincrement=True)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
