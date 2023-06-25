import json
import os
from dataclasses import dataclass

import spotipy
from flask import Flask, redirect, render_template, request, session
from spotipy.oauth2 import SpotifyOAuth



app = Flask(__name__)
app.secret_key = os.getenv("secret_key")

cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)


spotify = SpotifyOAuth(
    client_id=os.getenv("client_id"),
    client_secret=os.getenv("client_secret"),
    redirect_uri=os.getenv('redirect_uri')+"/callback",
    scope="user-top-read user-read-recently-played",
    cache_handler=cache_handler, show_dialog=True
)


@dataclass
class Track:
    name: str
    artist: str
    image: str
    link: str


@dataclass
class Artist:
    name: str
    image: str
    link: str


def group_artist(artists):
    artists_names = []
    for artist in artists:
        artists_names.append(artist.get("name", ""))
    return ", ".join(artists_names)


def clean_data(data: dict, type: str = "t"):
    if type == "t":
        tracks = []
        for item in data:
            try:
                ima = item["album"]["images"][0]["url"]
            except IndexError:
                ima = ""
            tracks.append(
                Track(
                    item.get("name"),
                    group_artist(item["artists"]),
                    ima,
                    item["external_urls"]["spotify"],
                )
            )
        return tracks
    if type == "r":
        tracks = []
        for item in data:
            item = item.get("track")
            tracks.append(
                Track(
                    item.get("name"),
                    group_artist(item["artists"]),
                    item["album"]["images"][0]["url"],
                    item["external_urls"]["spotify"],
                )
            )
        return tracks
    else:
        arts = []
        for item in data:
            arts.append(
                Artist(
                    item["name"],
                    item["images"][0]["url"],
                    item["external_urls"]["spotify"],
                )
            )
        return arts


def from_cache(file):
    with open(file, "r") as file:
        a = json.load(file)

    return a["items"]


@app.route("/")
def index():
    if not session.get("spotify_token"):
        return render_template("home.html", logged_in=False)
    return render_template("home.html", username=session.get('username'), profile_pic=session.get('profile_pic'))


@app.route("/top/tracks")
def tracks():
    if not session.get("spotify_token"):
        return redirect("/")
    sp = spotipy.Spotify(auth=session.get("spotify_token"))
    long_term_tracks = sp.current_user_top_tracks(time_range="long_term", limit=50)["items"]
    middle_term_tracks = sp.current_user_top_tracks(time_range="medium_term", limit=50)["items"]
    short_term_tracks = sp.current_user_top_tracks(time_range="short_term", limit=50)["items"]
    # long_term_tracks = from_cache('a.json')
    # short_term_tracks = from_cache('a.json')
    # middle_term_tracks = from_cache('a.json')
    return render_template(
        "list.html",
        lt=clean_data(long_term_tracks),
        mt=clean_data(middle_term_tracks),
        st=clean_data(short_term_tracks),
        username=session.get('username'), profile_pic=session.get('profile_pic')
    )


@app.route("/top/artists")
def artists():
    if not session.get("spotify_token"):
        return redirect("/")
    sp = spotipy.Spotify(auth=session.get("spotify_token"))
    long_term_artists = sp.current_user_top_artists(time_range="long_term", limit=50)["items"]
    middle_term_artists = sp.current_user_top_artists(time_range="medium_term", limit=50)["items"]
    short_term_artists = sp.current_user_top_artists(time_range="short_term", limit=50)["items"]
    # long_term_artists = from_cache('t.json')
    # short_term_artists = from_cache('t.json')
    # middle_term_artists = from_cache('t.json')
    return render_template(
        "list.html",
        lt=clean_data(long_term_artists, type="a"),
        mt=clean_data(middle_term_artists, type="a"),
        st=clean_data(short_term_artists, type="a"), username=session.get('username'), profile_pic=session.get('profile_pic')
    )


@app.route("/recents")
def recents():
    if not session.get("spotify_token"):
        return redirect("/")
    sp = spotipy.Spotify(auth=session.get("spotify_token"))
    tracks = sp.current_user_recently_played()["items"]
    # tracks = from_cache('r.json')
    return render_template("recents.html", t=clean_data(tracks, type="r"), username=session.get('username'), profile_pic=session.get('profile_pic'))


@app.route("/login")
def login():
    auth_url = spotify.get_authorize_url()
    return redirect(auth_url)

@app.route("/logout")
def logout():
    session.pop('spotify_token')
    session.clear()
    return redirect("/")


@app.route("/callback")
def callback():
    session.clear()
    code = request.args.get("code")
    token_info = spotify.get_access_token(code)
    session["spotify_token"] = token_info["access_token"]
    sp = spotipy.Spotify(auth=session.get("spotify_token"))
    user_profile = sp.current_user()
    session['username'] = user_profile['display_name']
    session['profile_pic'] = user_profile['images'][0]['url']

    return redirect("/")
