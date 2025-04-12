# yt-music-backup (YTMB)

A program for backing up a [YouTube Music](https://music.youtube.com) library.

yt-music-backup (YTMB) retrieves all playlist, track, artist, album and subscription data for a user from YouTube Music and store the information and relationships in an SQL database.

## Setup

The following setup instructions assume commands are run in a Bash shell. YTMB probably works with other systems, but none have been tested.

YTMB requires a working installation of [Poetry](https://python-poetry.org/), so following the [installation instructions](https://python-poetry.org/docs/#installation) in the documentation.

With a working poetry installation, create a virtual and environment and install the YTMB dependencies with:

```bash
poetry install
```

YTMB uses [ytmusicapi](https://github.com/sigma67/ytmusicapi) to get data from a YouTube Music library. This requires credentials to authenticate to the YouTube Data API. Instructions to obtain these credentials and set up the necessary files can be found on the ytmusicapi docs [here](https://ytmusicapi.readthedocs.io/en/stable/setup/oauth.html).

Once you have obtained a client ID and secret and created the `oath.json` file, make a copy of the `.env.example` file from this repository and call it `.env`:

```bash
cp .env.example .env
```

Now modify the `OATH_JSON`, `CLIENT_ID` and `CLIENT_SECRET` values.

The last piece of configuration is to set the path to the SQL database. By default, this uses a `ytmb.db` file in the working directory. Modify the `DB_URI` entry in `.env` if necessary.

## Usage

After following the above setup, running YTMB is as simple as setting the environment variables and running the main script:

```bash
set -a
source .env
cd ytmb
poetry run python main.py
```