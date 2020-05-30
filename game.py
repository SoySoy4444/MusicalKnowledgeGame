import os
import json
import spotipy
import spotipy.util as util
from spotipy import SpotifyException
from dotenv import load_dotenv
import random
import discord

load_dotenv()
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


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
                scope=scope,
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
        self.song = playlist.tracks["items"][self.index]
        print("SELF SONG")
        print(json.dumps(self.song, indent=4))

        self.artist_names = [artist["name"] for artist in self.song["track"]["artists"]] # there may be multiple artists
        self.album = self.song["track"]["album"]["name"]
        self.name = self.song["track"]["name"]

    def get_random_question(self):
        questions = {
            0: (f"Who is the artist of {self.name}?", self.artist_names),
            1: (f"What is the album name of {self.name}?", self.album),
        }

        question_number = random.randint(0, len(questions) - 1)
        random_question = questions[question_number][0]
        answer = questions[question_number][1]
        return random_question, answer


# Generate random playlist from a playlist dictionary
def get_random_playlist(playlist_dict):
    num_playlists = len(playlist_dict["items"])
    index = random.randint(0, num_playlists-1)
    random_playlist = playlist_dict["items"][index]
    return random_playlist


discord_client = discord.Client()
answer = None


async def next_question(current_playlist, channel):  # accepts a Playlist object
    song = current_playlist.get_random_song()
    global answer
    question, answer = song.get_random_question()

    await channel.send(question)


@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content.startswith("!user"):
        usernames = message.content.split(" ")[1:]
        await message.channel.send(f"Starting game with playlists by {usernames}")

        # https://developer.spotify.com/documentation/general/guides/scopes/
        scopes = "user-library-read"
        try:
            user = User("SoySoy4444", scopes)  # TODO: Change to username

            user_playlists = user.playlists

            playlists_names_list = [playlist["name"] for playlist in user_playlists["items"]]
            print(f"Hello {user.display_name}, you have the following playlists: {playlists_names_list}")
            current_playlist = Playlist(get_random_playlist(user_playlists), user.spotify_obj)
            print(f"We will start with... {current_playlist.name}!")

            await next_question(current_playlist, message.channel)
        except SpotifyException:
            await message.channel.send("Not a valid username!")

    if message.content.startswith("!featured"):
        oath = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        token = oath.get_access_token(as_dict=False)
        client = spotipy.client.Spotify(auth=token)

        featured_playlists = client.featured_playlists()["playlists"]
        featured_playlists_names = [s["name"] for s in featured_playlists["items"]]
        await message.channel.send(f"Today's featured playlists are: {featured_playlists_names}")

        current_playlist = Playlist(get_random_playlist(featured_playlists), client)
        print(f"We will start with... {current_playlist.name}!")

        await next_question(current_playlist, message.channel)

    if message.content.startswith("!playlist"):
        playlist_uri = message.content.split(" ")[1]


discord_client.run(DISCORD_TOKEN)
# https://discord.com/api/oauth2/authorize?client_id=715864951037755412&permissions=11264&scope=bot

# TODO: Add !skip command
# TODO: Add !hint command
# TODO: Check answers
# TODO: Add scoring system
