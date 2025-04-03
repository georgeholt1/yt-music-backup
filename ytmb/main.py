from tqdm import tqdm
from api_client import (
    get_all_playlists,
    get_playlist_tracks,
    get_all_albums,
    get_all_artists,
    get_all_subscriptions,
)
from db import (
    Session,
    initialize_database,
    store_playlists,
    store_track_from_playlist,
    store_user_saved_album,
    store_artist,
    store_subscribed_artist,
    store_albums_from_playlist,
)


def main():
    initialize_database()
    session = Session()

    all_playlists = get_all_playlists()

    store_playlists(session, all_playlists)

    for playlist in all_playlists:
        store_albums_from_playlist(session, playlist)
        tracks = get_playlist_tracks(playlist["playlistId"])
        for i, track in enumerate(tqdm(tracks)):
            store_track_from_playlist(session, playlist, track, i)

    all_albums = get_all_albums()
    for album in tqdm(all_albums):
        store_user_saved_album(session, album)

    all_artists = get_all_artists()
    for artist in tqdm(all_artists):
        store_artist(session, artist)

    all_subscriptions = get_all_subscriptions()
    for subscription in tqdm(all_subscriptions):
        if subscription["type"] == "artist":
            store_subscribed_artist(session, subscription)

    session.close()


if __name__ == "__main__":
    main()
