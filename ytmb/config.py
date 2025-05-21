import os
from sys import exit

try:
    DB_URI = os.environ["DB_URI"]
except KeyError:
    print("DB_URI environment variable not set. Aborting.")
    exit(1)

try:
    OATH_JSON = os.environ["OATH_JSON"]
except KeyError:
    print("OATH_JSON environment variable not set. Aborting.")
    exit(1)

try:
    CLIENT_ID = os.environ["CLIENT_ID"]
except KeyError:
    print("CLIENT_ID environment variable not set. Aborting.")
    exit(1)

try:
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]
except KeyError:
    print("CLIENT_SECRET environment variable not set. Aborting.")
    exit(1)
