import os
import json
import spotipy
import sys
import spotipy.util as util
from spotipy import SpotifyException
from dotenv import load_dotenv
import random

# username = sys.argv[0]
username = "SoySoy4444"
load_dotenv()
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# https://developer.spotify.com/documentation/general/guides/scopes/
scopes = "user-follow-read user-library-read playlist-read-private"

try:
    token = util.prompt_for_user_token(
        username,
        scope=scopes,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI
    )
except SpotifyException:
    os.remove(f".cache-{username}")
    token = util.prompt_for_user_token(
        username,
        scope=scopes,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI
    )

spotify_obj = spotipy.Spotify(auth=token)
user = spotify_obj.current_user()
print(json.dumps(user, sort_keys=True, indent=4))
