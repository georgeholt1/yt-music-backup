from tqdm import tqdm
from ytmb.api_client import (
    get_all_playlists,
    get_playlist_tracks,
    get_all_albums,
    get_all_artists,
    get_all_subscriptions,
)
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
    initialize_database()
    session = Session()

    print("Getting playlists")
    playlists = get_all_playlists()

    playlists = store_playlists(session, playlists)

    print("Storing playlist tracks")
    for playlist in tqdm(playlists):
        tracks = get_playlist_tracks(playlist["ytmusic_id"])
        store_artists_from_tracks(session, tracks)
        store_albums_from_tracks(session, tracks)
        for i, track in enumerate(tracks):
            store_track_from_playlist(session, playlist["playlist_table_id"], track, i)

    print("Getting albums")
    all_albums = get_all_albums()
    for album in tqdm(all_albums):
        store_user_saved_album(session, album)

    print("Getting artists")
    all_artists = get_all_artists()
    for artist in tqdm(all_artists):
        store_artist_from_artist_data(session, artist)

    print("Getting subscriptions")
    all_subscriptions = get_all_subscriptions()
    for subscription in tqdm(all_subscriptions):
        if subscription["type"] == "artist":
            store_artist_from_artist_data(session, subscription, user_saved=True)

    session.close()

    print("Done")


if __name__ == "__main__":
    main()
