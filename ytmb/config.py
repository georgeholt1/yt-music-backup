import os

try:
    DB_URI = os.environ["DB_URI"]
except KeyError:
    print("DB_URI environment variable not set. Aborting.")
    exit(1)
