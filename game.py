import os
import json
import spotipy
import spotipy.util as util
from spotipy import SpotifyException
from dotenv import load_dotenv
import random

load_dotenv()
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")


class User:
    def __init__(self, username, scope):
        try:
            self.token = util.prompt_for_user_token(
                username,
                scope=scope,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI
            )
        except SpotifyException:
            os.remove(f".cache-{username}")
            self.token = util.prompt_for_user_token(
                username,
                scope=scopes,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI
            )

        self.spotify_obj = spotipy.Spotify(auth=self.token)
        self.user = self.spotify_obj.current_user()

        self.display_name = self.user["display_name"]
        self.followers = self.user["followers"]["total"]
        self.uri = self.user["uri"]

        # https://developer.spotify.com/documentation/web-api/reference/playlists/get-a-list-of-current-users-playlists/
        self.playlists = self.spotify_obj.user_playlists(username)


# https://developer.spotify.com/documentation/general/guides/scopes/
scopes = "user-follow-read user-library-read playlist-read-private"
user = User("SoySoy4444", scopes)
user_playlists = user.playlists
playlists_names_list = [playlist["name"] for playlist in user_playlists["items"]]

print(f"Welcome, {user.display_name}!")
print(f"You have {user.followers} followers.")
print("You have the following playlists: ")
print(playlists_names_list)
print()
