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
    store_artist_from_artist_data,
    store_albums_from_tracks,
    store_artists_from_tracks,
)


def main():
    initialize_database()
    session = Session()

    all_playlists = get_all_playlists()

    store_playlists(session, all_playlists)

    for playlist in all_playlists:
        tracks = get_playlist_tracks(playlist["playlistId"])
        store_artists_from_tracks(session, tracks)
        store_albums_from_tracks(session, tracks)
        for i, track in enumerate(tqdm(tracks)):
            store_track_from_playlist(session, playlist, track, i)

    all_albums = get_all_albums()
    for album in tqdm(all_albums):
        store_user_saved_album(session, album)

    all_artists = get_all_artists()
    for artist in tqdm(all_artists):
        store_artist_from_artist_data(session, artist)

    all_subscriptions = get_all_subscriptions()
    for subscription in tqdm(all_subscriptions):
        if subscription["type"] == "artist":
            store_artist_from_artist_data(session, subscription, user_saved=True)

    session.close()


if __name__ == "__main__":
    main()
