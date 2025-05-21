import argparse
from tqdm import tqdm
from ytmb.api_client import (
    get_library_state,
    get_playlist_tracks,
)
from ytmb.all_playlist import handle_ytmb_all_playlist
from ytmb.db import (
    Session,
    initialize_database,
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
    playlists, all_albums, all_artists, all_subscriptions = get_library_state()

    print("Storing playlists")
    playlists = store_playlists(session, playlists)

    print("Storing playlist tracks")
    for playlist in tqdm(playlists):
        if playlist["name"] == "ytmb-all":
            continue
        tracks = get_playlist_tracks(playlist["ytmusic_id"])
        store_artists_from_tracks(session, tracks)
        store_albums_from_tracks(session, tracks)
        for i, track in enumerate(tracks):
            store_track_from_playlist(session, playlist["playlist_table_id"], track, i)

    print("Storing albums")
    for album in tqdm(all_albums):
        store_user_saved_album(session, album)

    print("Storing artists")
    for artist in tqdm(all_artists):
        store_artist_from_artist_data(session, artist)

    print("Storing subscriptions")
    for subscription in tqdm(all_subscriptions):
        if subscription["type"] == "artist":
            store_artist_from_artist_data(session, subscription, user_saved=True)

    if args.all_playlist:
        print("Handling all-playlist")
        handle_ytmb_all_playlist(playlists, session)

    session.close()

    print("Done")


if __name__ == "__main__":
    main()
