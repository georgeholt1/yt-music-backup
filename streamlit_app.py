import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ytmb.config import DB_URI
from ytmb.models import Artist, Track, Album, Playlist, TrackArtist, PlaylistTrack


# Initialize database connection
@st.cache_resource
def init_db():
    engine = create_engine(DB_URI)
    Session = sessionmaker(bind=engine)
    return Session


def get_session():
    Session = init_db()
    return Session()


# Main app
def main():
    st.set_page_config(page_title="YTMB Database Browser", layout="wide")
    st.title("🎵 YouTube Music Backup - Database Browser")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a view:", ["Overview", "Artists", "Albums", "Tracks", "Playlists"]
    )

    if page == "Overview":
        show_overview()
    elif page == "Artists":
        show_artists()
    elif page == "Albums":
        show_albums()
    elif page == "Tracks":
        show_tracks()
    elif page == "Playlists":
        show_playlists()


def show_overview():
    st.header("Database Overview")

    session = get_session()

    # Get counts
    artist_count = session.query(Artist).count()
    track_count = session.query(Track).count()
    album_count = session.query(Album).count()
    playlist_count = session.query(Playlist).count()

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Artists", artist_count)

    with col2:
        st.metric("Tracks", track_count)

    with col3:
        st.metric("Albums", album_count)

    with col4:
        st.metric("Playlists", playlist_count)

    # User saved counts
    st.subheader("User Saved Items")

    user_saved_artists = session.query(Artist).filter(Artist.user_saved).count()
    user_saved_albums = session.query(Album).filter(Album.user_saved).count()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("User Saved Artists", user_saved_artists)
    with col2:
        st.metric("User Saved Albums", user_saved_albums)

    session.close()


def show_artists():
    st.header("Artists")

    session = get_session()

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        show_user_saved = st.checkbox("Show only user saved", False)
    with col2:
        search_term = st.text_input("Search artists:", "")

    # Query artists
    query = session.query(Artist)

    if show_user_saved:
        query = query.filter(Artist.user_saved)

    if search_term:
        query = query.filter(Artist.name.ilike(f"%{search_term}%"))

    artists = query.order_by(Artist.name).all()

    # Display results
    st.write(f"Found {len(artists)} artists")

    if artists:
        artist_data = [
            {
                "Name": artist.name,
                "User Saved": "✓" if artist.user_saved else "",
                "Track Count": len(artist.tracks),
            }
            for artist in artists
        ]

        df = pd.DataFrame(artist_data)
        st.dataframe(df, use_container_width=True)

    session.close()


def show_albums():
    st.header("Albums")

    session = get_session()

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        show_user_saved = st.checkbox("Show only user saved", False)
    with col2:
        search_term = st.text_input("Search albums:", "")

    # Query albums
    query = session.query(Album)

    if show_user_saved:
        query = query.filter(Album.user_saved)

    if search_term:
        query = query.filter(Album.name.ilike(f"%{search_term}%"))

    albums = query.order_by(Album.name).all()

    # Display results
    st.write(f"Found {len(albums)} albums")

    if albums:
        album_data = [
            {
                "Name": album.name,
                "User Saved": "✓" if album.user_saved else "",
                "Track Count": len(album.tracks) if hasattr(album, "tracks") else 0,
            }
            for album in albums
        ]

        df = pd.DataFrame(album_data)
        st.dataframe(df, use_container_width=True)

    session.close()


def show_tracks():
    st.header("Tracks")

    session = get_session()

    # Search filter
    search_term = st.text_input("Search tracks:", "")

    # Query tracks with related data
    query = session.query(Track).join(Album)

    if search_term:
        query = query.filter(Track.name.ilike(f"%{search_term}%"))

    tracks = query.order_by(Track.name).limit(1000).all()  # Limit for performance

    # Display results
    st.write(f"Showing {len(tracks)} tracks (limited to 1000 for performance)")

    if tracks:
        track_data = []
        for track in tracks:
            # Get artists for this track
            track_artists = (
                session.query(TrackArtist).filter_by(track_id=track.id).all()
            )
            artist_names = [ta.artist.name for ta in track_artists]

            track_data.append(
                {
                    "Track": track.name,
                    "Artists": ", ".join(artist_names),
                    "Album": track.album.name if track.album else "",
                    "YouTube Music ID": track.ytmusic_id,
                }
            )

        df = pd.DataFrame(track_data)
        st.dataframe(df, use_container_width=True)

    session.close()


def show_playlists():
    st.header("Playlists")

    session = get_session()

    # Search filter
    search_term = st.text_input("Search playlists:", "")

    # Query playlists
    query = session.query(Playlist)

    if search_term:
        query = query.filter(Playlist.title.ilike(f"%{search_term}%"))

    playlists = query.order_by(Playlist.title).all()

    # Display results
    st.write(f"Found {len(playlists)} playlists")

    if playlists:
        # Playlist overview
        playlist_data = []
        for playlist in playlists:
            track_count = (
                session.query(PlaylistTrack).filter_by(playlist_id=playlist.id).count()
            )
            playlist_data.append(
                {"Playlist": playlist.title, "Track Count": track_count}
            )

        df = pd.DataFrame(playlist_data)
        st.dataframe(df, use_container_width=True)

        # Detailed view for selected playlist
        if playlists:
            st.subheader("Playlist Details")
            selected_playlist = st.selectbox(
                "Select a playlist to view details:",
                options=[p.title for p in playlists],
                index=0,
            )

            if selected_playlist:
                playlist_obj = next(
                    p for p in playlists if p.title == selected_playlist
                )

                # Get tracks in this playlist
                playlist_tracks = (
                    session.query(PlaylistTrack, Track, Album)
                    .join(Track, PlaylistTrack.track_id == Track.id)
                    .join(Album, Track.album_id == Album.id)
                    .filter(PlaylistTrack.playlist_id == playlist_obj.id)
                    .order_by(PlaylistTrack.position)
                    .all()
                )

                if playlist_tracks:
                    track_details = []
                    for pt, track, album in playlist_tracks:
                        # Get artists for this track
                        track_artists = (
                            session.query(TrackArtist)
                            .filter_by(track_id=track.id)
                            .all()
                        )
                        artist_names = [ta.artist.name for ta in track_artists]

                        track_details.append(
                            {
                                "Position": pt.position,
                                "Track": track.name,
                                "Artists": ", ".join(artist_names),
                                "Album": album.name,
                            }
                        )

                    df_tracks = pd.DataFrame(track_details)
                    st.dataframe(df_tracks, use_container_width=True)
                else:
                    st.info("This playlist has no tracks.")

    session.close()


if __name__ == "__main__":
    main()
