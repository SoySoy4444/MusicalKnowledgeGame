import os
import json
import spotipy
import spotipy.util as util
from spotipy import SpotifyException
from dotenv import load_dotenv
import random
from discord.ext import commands

load_dotenv()
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
discord_client = commands.Bot(command_prefix="!")

oauth = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
token = oauth.get_access_token(as_dict=False)
spotipy_client = spotipy.client.Spotify(auth=token)

current_playlist, correct_answer, mode, game_playlists_iterator = None, "", None, iter([])


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
    def __init__(self, playlist_dict, spotify_obj):  # accepts a playlist dictionary
        self.name = playlist_dict["name"]
        self.id = playlist_dict["id"]
        self.tracks = spotify_obj.playlist_tracks(self.id)
        self.song_names = [track["track"]["name"] for track in self.tracks["items"]]

    def get_random_song(self):
        return Song(self)


class Song:
    def __init__(self, playlist_obj):  # accepts a Playlist object
        self.playlist = playlist_obj
        self.num_songs = len(self.playlist.tracks["items"])
        self.index = random.randint(0, self.num_songs-1)
        self.song = self.playlist.tracks["items"][self.index]

        self.artist_names = [artist["name"] for artist in self.song["track"]["artists"]]  # possibly multiple artists
        self.album = self.song["track"]["album"]["name"]
        self.name = self.song["track"]["name"]

        self.used_songs_indices = [self.index]  # stores the indices of songs used for the correct answer and decoys

    def get_random_question(self):
        questions = {
            0: (f"Who is the artist of {self.name}?", " & ".join(self.artist_names)),
            1: (f"What is the album name of {self.name}?", self.album),
        }
        question_type = random.randint(0, len(questions) - 1)
        random_question = questions[question_type][0]
        correct_answer_ = questions[question_type][1]

        choices = ["A) ", "B) ", "C) ", "D) "]

        answers_list = []  # multiple choice answers
        correct_answer_index = random.randint(0, 3)  # the index of the correct answer, 0 - 3.
        for i in range(len(choices)):  # for each answer choice
            if i == correct_answer_index:  # for the correct answer,
                answers_list.append(choices[i] + correct_answer_)
                continue

            while True:
                if (random_song_index := random.randint(0, self.num_songs-1)) not in self.used_songs_indices:
                    self.used_songs_indices.append(random_song_index)
                    break
            random_song = self.playlist.tracks["items"][random_song_index]
            if question_type == 0:
                random_song_artists = [artist["name"] for artist in random_song["track"]["artists"]]
                answers_list.append(choices[i] + " & ".join(random_song_artists))
            elif question_type == 1:
                answers_list.append(choices[i] + random_song["track"]["album"]["name"])

        return random_question, answers_list, correct_answer_index


async def next_question(playlist_obj, channel):  # accepts a Playlist object
    song = playlist_obj.get_random_song()
    global correct_answer
    question, answer_choices, correct_index = song.get_random_question()

    correct_answer = answer_choices[correct_index]  # set the correct answer to a variable
    await channel.send(question)  # send question
    await channel.send("\n".join([answer_choice for answer_choice in answer_choices]))  # send answer choices


@discord_client.event
async def on_message(message):
    global current_playlist, mode, game_playlists_iterator
    if message.author == discord_client.user:
        return

    elif message.content in correct_answer and ")" in message.content:
        await message.channel.send(f"Correct, it's {correct_answer}!")
        await next_question(current_playlist, message.channel)

    await discord_client.process_commands(message)
    # https://discordpy.readthedocs.io/en/rewrite/faq.html#why-does-on-message-make-my-commands-stop-working
    # Overriding on_message prevents commands from running, so add client.process_commands(message)


@discord_client.command(pass_context=True)
async def nextplaylist(ctx):
    if mode is None:
        await ctx.send("Initialise the game with !user <username>, !featured or !playlist <uri> first!")
    elif mode == "playlist":
        await ctx.send("You cannot move on to the next playlist on playlist mode!")
    else:
        try:
            global current_playlist
            current_playlist = Playlist(next(game_playlists_iterator), spotipy_client)

            await ctx.send(f"Next playlist coming up! Now playing... {current_playlist.name}!")
            await next_question(current_playlist, ctx.message.channel)
        except StopIteration:
            await ctx.send("You have played all playlists!")


@discord_client.command(pass_context=True)
async def user(ctx, *args):
    global mode, current_playlist, game_playlists_iterator
    mode = "user"
    username = args[0]
    await ctx.send(f"Starting game with playlists by {username}")

    # https://developer.spotify.com/documentation/general/guides/scopes/
    scopes = "user-library-read"
    try:
        user_obj = User(username, scopes)

        user_playlists = user_obj.playlists
        global spotipy_client
        spotipy_client = user_obj.spotify_obj  # before, client was only Spotify API, but now we need user access.

        playlists_names_list = [playlis["name"] for playlis in user_playlists["items"]]
        print(f"Hello {user_obj.display_name}, you have the following playlists: {playlists_names_list}")

        game_playlists = user_playlists["items"]
        random.shuffle(game_playlists)
        game_playlists_iterator = iter(game_playlists)
        current_playlist = Playlist(next(game_playlists_iterator), spotipy_client)
        await ctx.send(f"We will start with... {current_playlist.name}!")

        await next_question(current_playlist, ctx.message.channel)
    except SpotifyException:  # Authentication failed.
        await ctx.send("Not a valid username!")


@discord_client.command(pass_context=True)
async def featured(ctx):
    print("TRIGGERRRRR")
    global mode, current_playlist, game_playlists_iterator
    mode = "featured"
    featured_playlists = spotipy_client.featured_playlists()["playlists"]
    featured_playlists_names = [playlis["name"] for playlis in featured_playlists["items"]]
    await ctx.send(f"Today's featured playlists are: {featured_playlists_names}")

    game_playlists = featured_playlists["items"]
    random.shuffle(game_playlists)
    game_playlists_iterator = iter(game_playlists)
    current_playlist = Playlist(next(game_playlists_iterator), spotipy_client)
    await ctx.send(f"We will start with... {current_playlist.name}!")

    await next_question(current_playlist, ctx.message.channel)


@discord_client.command(pass_context=True)
async def playlist(ctx):
    global mode, current_playlist
    mode = "playlist"
    playlist_uri = ctx.message.content.split(" ")[1]
    current_playlist = Playlist(spotipy_client.playlist(playlist_uri), spotipy_client)
    await ctx.send(f"Starting game on {current_playlist.name}!")
    await next_question(current_playlist, ctx.message.channel)

discord_client.run(DISCORD_TOKEN)
# https://discord.com/api/oauth2/authorize?client_id=715864951037755412&permissions=11264&scope=bot

# TODO: Add !skip command
# TODO: Add !hint command
# TODO: Add scoring system
