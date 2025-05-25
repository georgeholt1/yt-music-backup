import argparse
from tqdm import tqdm
from ytmb.api_client import (
    get_library_state,
    get_playlist_tracks,
)
from ytmb.all_playlist import handle_ytmb_all_playlist
from ytmb.db import (
    Session,
    identify_albums_to_remove,
    identify_artists_to_remove,
    identify_playlists_to_remove,
    identify_tracks_to_remove,
    initialize_database,
    remove_albums,
    remove_artists,
    remove_playlists,
    remove_tracks,
    store_playlists,
    store_track_from_playlist,
    store_user_saved_album,
    store_artist_from_artist_data,
    store_albums_from_tracks,
    store_artists_from_tracks,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--all-playlist",
        action="store_true",
        help="Create an amalgamation playlist of library music",
    )
    args = parser.parse_args()

    initialize_database()
    session = Session()

    pbar = tqdm(total=8)

    pbar.set_description("Getting YTMusic library")
    playlists, library_albums, library_artists, library_subscriptions = (
        get_library_state()
    )
    pbar.update()
    all_artist_names = set.union(
        set([a["artist"] for a in library_artists]),
        set([a["artist"] for a in library_subscriptions]),
    )
    all_album_names = set([a["title"] for a in library_albums])

    all_track_titles = []

    pbar.set_description("Storing playlists")
    playlists = store_playlists(session, playlists)
    pbar.update()

    pbar.set_description("Storing playlist tracks")
    pbar_playlists = tqdm(playlists, position=1, leave=False)
    for playlist in pbar_playlists:
        pbar_playlists.set_description(playlist["name"])
        if playlist["name"] == "ytmb-all":
            continue

        tracks = get_playlist_tracks(playlist["ytmusic_id"])
        all_track_titles.extend([t["title"] for t in tracks])

        artists = store_artists_from_tracks(session, tracks)
        all_artist_names = set(all_artist_names).union(artists)

        albums = store_albums_from_tracks(session, tracks)
        all_album_names = set(all_album_names).union(albums)

        for i, track in enumerate(tqdm(tracks, position=2, leave=False, desc="Tracks")):
            store_track_from_playlist(session, playlist["playlist_table_id"], track, i)

    pbar.update()

    pbar.set_description("Storing albums")
    for album in tqdm(library_albums, position=1, leave=False):
        store_user_saved_album(session, album)
    pbar.update()

    pbar.set_description("Storing artists")
    for artist in tqdm(library_artists, position=1, leave=False):
        store_artist_from_artist_data(session, artist)
    pbar.update()

    pbar.set_description("Storing subscriptions")
    for subscription in tqdm(library_subscriptions, position=1, leave=False):
        if subscription["type"] == "artist":
            store_artist_from_artist_data(session, subscription, user_saved=True)
    pbar.update()

    if args.all_playlist:
        pbar.set_description("Handling all-playlist")
        handle_ytmb_all_playlist(playlists, session)
    pbar.update()

    pbar.set_description("Cleaning up database")
    playlists_to_remove = identify_playlists_to_remove(session, playlists)
    remove_playlists(session, playlists_to_remove)
    artists_to_remove = identify_artists_to_remove(session, all_artist_names)
    remove_artists(session, artists_to_remove)
    albums_to_remove = identify_albums_to_remove(session, all_album_names)
    remove_albums(session, albums_to_remove)
    tracks_to_remove = identify_tracks_to_remove(session, all_track_titles)
    remove_tracks(session, tracks_to_remove)
    pbar.update()

    session.close()

    pbar.close()

    print("Done")


if __name__ == "__main__":
    main()
