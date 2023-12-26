from flask import Flask, url_for, request, session, redirect, render_template
import spotipy
import time
from datetime import date
from spotipy.oauth2 import SpotifyOAuth
from credentials import CLIENT_ID, CLIENT_SECRET, SECRET_KEY

TOKEN_CODE = "token_info"

scope = "user-top-read user-library-read user-read-recently-played user-library-read"

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route("/")
def hello_world():
    return render_template('index.html', title="Welcome")

@app.route("/login")
def login():
    sp_oauth = SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = url_for("redirectPage", _external = True),
        scope = scope
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/redirectPage")
def redirectPage():
    code = request.args.get('code')
    sp_oauth = SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = url_for("redirectPage", _external = True),
        scope = scope
    )

    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_CODE] = token_info
    session.modified = True
    return redirect("receipt")

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=url_for("redirectPage",_external=True), 
        scope = scope
    )

def get_token():
    token_info = session.get(TOKEN_CODE, None)
    if not token_info: 
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60 
    if (is_expired): 
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info 

@app.route("/receipt")
def receipt():
    user_token = get_token()
    sp = spotipy.Spotify(
        auth = user_token['access_token']
    )
    current_user_id = sp.current_user()['id']
    current_user_name = sp.current_user()['display_name']
    short_term_tracks = sp.current_user_top_tracks(
        limit = 10,
        offset = 0,
        time_range='short_term'
    )
    medium_term_tracks = sp.current_user_top_tracks(
        limit = 10,
        offset = 0,
        time_range='medium_term'    )
    long_term_tracks = sp.current_user_top_tracks(
        limit = 10,
        offset = 0,
        time_range='long_term'    )
    short_term_artists = sp.current_user_top_artists(
        limit = 10,
        offset = 0,
        time_range='short_term'
    )
    medium_term_artists = sp.current_user_top_artists(
        limit = 10,
        offset = 0,
        time_range='medium_term'    )
    long_term_artists = sp.current_user_top_artists(
        limit = 10,
        offset = 0,
        time_range='long_term'    )
    
    track_seed = []
    for song in short_term_tracks['items']:
        if len(track_seed) < 2:
            track_seed.append(song['id'])

    artist_seed = []
    for artist in short_term_artists['items']:
        if len(artist_seed) < 2:
            artist_seed.append(artist['id'])

    return render_template('receipt.html', create_playlist = create_playlist, current_user_id = current_user_id, user_display_name = current_user_name, currentTime=date.today().strftime("%B %d, %Y"), currentYear=date.today().strftime("%Y"), short_term_tracks = short_term_tracks, medium_term_tracks = medium_term_tracks, long_term_tracks = long_term_tracks, short_term_artists = short_term_artists, medium_term_artists = medium_term_artists, long_term_artists = long_term_artists, sp = sp, track_seed = track_seed, artist_seed = artist_seed)

@app.template_filter('mmss')
def _jinja2_filter_miliseconds(time, fmt=None):
    time = int(time / 1000)
    minutes = time // 60 
    seconds = time % 60 
    if seconds < 10: 
        return str(minutes) + ":0" + str(seconds)
    return str(minutes) + ":" + str(seconds ) 

@app.template_filter('create_playlist')
def create_playlist(sp, current_user_id, user_display_name, track_seed, artist_seed):
    playlist = sp.user_playlist_create(current_user_id,"for " + user_display_name,public=False,collaborative=False, description="")
    playlist_id = playlist["id"]
    songs = sp.recommendations(seed_artists=artist_seed, seed_genres=None, seed_tracks=track_seed, limit=15, country=None)
    for song in songs["tracks"]:
        recommended = sp.playlist_add_items(playlist_id, [song["uri"]], position=None)

    return ""