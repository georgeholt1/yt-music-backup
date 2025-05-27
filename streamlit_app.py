import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ytmb.config import DB_URI
from ytmb.models import Artist, Track, Album, Playlist, TrackArtist, PlaylistTrack


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

    query = session.query(Artist)

    if show_user_saved:
        query = query.filter(Artist.user_saved)

    if search_term:
        query = query.filter(Artist.name.ilike(f"%{search_term}%"))

    artists = query.order_by(Artist.name).all()

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

        # Artist details section
        if artists:
            st.subheader("Artist Details")
            selected_artist_name = st.selectbox(
                "Select an artist to view details:",
                options=[artist.name for artist in artists],
                index=0,
            )

            if selected_artist_name:
                selected_artist = next(
                    artist for artist in artists if artist.name == selected_artist_name
                )
                show_artist_details(session, selected_artist)

    session.close()


def show_artist_details(session, artist):
    """Show detailed information for a selected artist"""

    tab1, tab2 = st.tabs(["Tracks", "Albums"])

    with tab1:
        st.subheader(f"Tracks by {artist.name}")

        # Get all tracks by this artist
        track_artists = session.query(TrackArtist).filter_by(artist_id=artist.id).all()

        if track_artists:
            track_data = []
            for ta in track_artists:
                track = ta.track

                # Get all artists for this track (for collaborations)
                all_track_artists = (
                    session.query(TrackArtist).filter_by(track_id=track.id).all()
                )
                all_artist_names = [ata.artist.name for ata in all_track_artists]

                track_data.append(
                    {
                        "Track": track.name,
                        "All Artists": ", ".join(all_artist_names),
                        "Album": track.album.name if track.album else "",
                        "YouTube Music ID": track.ytmusic_id,
                    }
                )

            df_tracks = pd.DataFrame(track_data)
            st.dataframe(df_tracks, use_container_width=True)
            st.write(f"Total tracks: {len(track_data)}")
        else:
            st.info(f"No tracks found for {artist.name}")

    with tab2:
        st.subheader(f"Albums featuring {artist.name}")

        # Get unique albums that contain tracks by this artist
        albums_query = (
            session.query(Album)
            .join(Track, Track.album_id == Album.id)
            .join(TrackArtist, TrackArtist.track_id == Track.id)
            .filter(TrackArtist.artist_id == artist.id)
            .distinct()
            .order_by(Album.name)
        )

        albums = albums_query.all()

        if albums:
            album_data = []
            for album in albums:
                # Count tracks by this artist in this album
                artist_tracks_in_album = (
                    session.query(Track)
                    .join(TrackArtist)
                    .filter(Track.album_id == album.id)
                    .filter(TrackArtist.artist_id == artist.id)
                    .count()
                )

                # Total tracks in album
                total_tracks_in_album = (
                    session.query(Track).filter(Track.album_id == album.id).count()
                )

                album_data.append(
                    {
                        "Album": album.name,
                        "Artist Tracks": artist_tracks_in_album,
                        "Total Tracks": total_tracks_in_album,
                        "User Saved": "✓" if album.user_saved else "",
                    }
                )

            df_albums = pd.DataFrame(album_data)
            st.dataframe(df_albums, use_container_width=True)
            st.write(f"Total albums: {len(album_data)}")

            # Show detailed album view
            if albums:
                st.subheader("Album Track Details")
                selected_album_name = st.selectbox(
                    f"Select an album to see {artist.name}'s tracks:",
                    options=[album.name for album in albums],
                    key="artist_album_select",
                )

                if selected_album_name:
                    selected_album = next(
                        album for album in albums if album.name == selected_album_name
                    )

                    # Get tracks by this artist in the selected album
                    artist_album_tracks = (
                        session.query(Track)
                        .join(TrackArtist)
                        .filter(Track.album_id == selected_album.id)
                        .filter(TrackArtist.artist_id == artist.id)
                        .order_by(Track.name)
                        .all()
                    )

                    if artist_album_tracks:
                        album_track_data = []
                        for track in artist_album_tracks:
                            # Get all artists for this track
                            all_track_artists = (
                                session.query(TrackArtist)
                                .filter_by(track_id=track.id)
                                .all()
                            )
                            all_artist_names = [
                                ata.artist.name for ata in all_track_artists
                            ]

                            album_track_data.append(
                                {
                                    "Track": track.name,
                                    "All Artists": ", ".join(all_artist_names),
                                    "YouTube Music ID": track.ytmusic_id,
                                }
                            )

                        df_album_tracks = pd.DataFrame(album_track_data)
                        st.dataframe(df_album_tracks, use_container_width=True)
                    else:
                        st.info(
                            f"No tracks by {artist.name} found in {selected_album_name}"
                        )
        else:
            st.info(f"No albums found featuring {artist.name}")


def show_albums():
    st.header("Albums")

    session = get_session()

    col1, col2 = st.columns(2)
    with col1:
        show_user_saved = st.checkbox("Show only user saved", False)
    with col2:
        search_term = st.text_input("Search albums:", "")

    query = session.query(Album)

    if show_user_saved:
        query = query.filter(Album.user_saved)

    if search_term:
        query = query.filter(Album.name.ilike(f"%{search_term}%"))

    albums = query.order_by(Album.name).all()

    st.write(f"Found {len(albums)} albums")

    if albums:
        album_data = []
        for album in albums:
            # Get unique artists for this album
            artists_query = (
                session.query(Artist)
                .join(TrackArtist, TrackArtist.artist_id == Artist.id)
                .join(Track, Track.id == TrackArtist.track_id)
                .filter(Track.album_id == album.id)
                .distinct()
                .order_by(Artist.name)
            )

            artists = artists_query.all()
            artist_names = [artist.name for artist in artists]

            album_data.append(
                {
                    "Name": album.name,
                    "Artists": ", ".join(artist_names) if artist_names else "Unknown",
                    "User Saved": "✓" if album.user_saved else "",
                    "Track Count": len(album.tracks) if hasattr(album, "tracks") else 0,
                }
            )

        df = pd.DataFrame(album_data)
        st.dataframe(df, use_container_width=True)

    session.close()


def show_tracks():
    st.header("Tracks")

    session = get_session()

    search_term = st.text_input("Search tracks:", "")

    query = session.query(Track).join(Album)

    if search_term:
        query = query.filter(Track.name.ilike(f"%{search_term}%"))

    tracks = query.order_by(Track.name).all()

    st.write(f"Showing {len(tracks)} tracks")

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

    search_term = st.text_input("Search playlists:", "")

    query = session.query(Playlist)

    if search_term:
        query = query.filter(Playlist.title.ilike(f"%{search_term}%"))

    playlists = query.order_by(Playlist.title).all()

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
