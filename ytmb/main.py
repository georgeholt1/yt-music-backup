import argparse
from tqdm import tqdm
from ytmb.api_client import (
    get_library_state,
    get_playlist_tracks,
)
from ytmb.all_playlist import handle_ytmb_all_playlist
from ytmb.db import (
    Session,
    identify_artists_to_remove,
    identify_playlists_to_remove,
    initialize_database,
    remove_artists,
    remove_playlists,
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

    print("Getting YTMusic library")
    playlists, library_albums, library_artists, library_subscriptions = (
        get_library_state()
    )
    all_artist_names = set.union(
        set([a["artist"] for a in library_artists]),
        set([a["artist"] for a in library_subscriptions]),
    )

    print("Storing playlists")
    playlists = store_playlists(session, playlists)

    print("Storing playlist tracks")
    for playlist in tqdm(playlists):
        if playlist["name"] == "ytmb-all":
            continue
        tracks = get_playlist_tracks(playlist["ytmusic_id"])
        artists = store_artists_from_tracks(session, tracks)
        all_artist_names = set(all_artist_names).union(artists)
        store_albums_from_tracks(session, tracks)
        for i, track in enumerate(tracks):
            store_track_from_playlist(session, playlist["playlist_table_id"], track, i)

    print("Storing albums")
    for album in tqdm(library_albums):
        store_user_saved_album(session, album)

    print("Storing artists")
    for artist in tqdm(library_artists):
        store_artist_from_artist_data(session, artist)

    print("Storing subscriptions")
    for subscription in tqdm(library_subscriptions):
        if subscription["type"] == "artist":
            store_artist_from_artist_data(session, subscription, user_saved=True)

    if args.all_playlist:
        print("Handling all-playlist")
        handle_ytmb_all_playlist(playlists, session)

    print("Cleaning up database")
    playlists_to_remove = identify_playlists_to_remove(session, playlists)
    remove_playlists(session, playlists_to_remove)
    artists_to_remove = identify_artists_to_remove(session, all_artist_names)
    remove_artists(session, artists_to_remove)

    session.close()

    print("Done")


if __name__ == "__main__":
    main()
