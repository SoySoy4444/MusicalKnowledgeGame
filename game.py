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


class Playlist:
    def __init__(self, playlist, spotify_obj):  # accepts a playlist dictionary
        self.name = playlist["name"]
        self.id = playlist["id"]
        self.tracks = spotify_obj.playlist_tracks(self.id)
        self.song_names = [track["track"]["name"] for track in self.tracks["items"]]

    def get_random_song(self):
        return Song(self)


class Song:
    def __init__(self, playlist):  # accepts a Playlist object
        self.num_songs = len(playlist.tracks["items"])
        self.index = random.randint(0, self.num_songs-1)


# https://developer.spotify.com/documentation/general/guides/scopes/
scopes = "user-follow-read user-library-read playlist-read-private"
try:
    user = User("SoySoy4444", scopes)
except SpotifyException:
    print("Not a valid username!")

user_playlists = user.playlists
playlists_names_list = [playlist["name"] for playlist in user_playlists["items"]]

print(f"Welcome, {user.display_name}!")
print(f"You have {user.followers} followers.")
print("You have the following playlists: ")
print(playlists_names_list)
print()

# Generate random playlist
index = random.randint(0, len(user_playlists["items"])-1)
random_playlist = user_playlists["items"][index]
current_playlist = Playlist(random_playlist, user.spotify_obj)

print(f"Starting quiz on... {current_playlist.name}!")
print(current_playlist.song_names)

if __name__ == "__main__":
    while (x := input("Enter: ")) != "q":
        print("Hi")
        if x.startswith("!user"):
            usernames = x.split(" ")[1:]
            print(usernames)
        elif x.startswith("!playlist"):
            playlist_uri = x.split(" ")[1]
            print("Ok")
        elif x.startswith("!featured"):
            oath = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
            token = oath.get_access_token(as_dict=False)
            client = spotipy.client.Spotify(auth=token)

            featured_playlists = client.featured_playlists()
            print(json.dumps(featured_playlists, indent=4))