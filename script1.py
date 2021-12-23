# To run flask
# $ export FLASK_APP=backend.py
# $ export FLASK_ENV=development
# $ flask run (note: if you want to run on different local port, run 'python3 backend.py' instead)

from flask import Flask, request, url_for, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import requests
from urllib.parse import urlencode
#import base64

# SPOTIFY END POINTS
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize?' # url where user is asked to login and to give permission. 
# We redirect user to this url and also provide the required information to Spotify, we then get a code in return from Spotify.
# We can grab the code from the argument of our callback url.

SPOTIFY_ACCESS_TOKEN_URL = 'https://accounts.spotify.com/api/token' # url where we can get the token info by providing the code. 
# Using the code that we got by requesting to the above url as one of the parameters, we can get the token info from Spotify.
# Token info consists of the access token, the expiration time, and the refresh token.

SPOTIFY_GET_CURRENT_TRACK_URL = 'https://api.spotify.com/v1/me/player/currently-playing' # end point to get user current track

SPOTIFY_GET_USER_PROFILE_URL = 'https://api.spotify.com/v1/me' # end point to get user account information
# end of SPOTIFY END POINTS

# SPOTIFY DEVELOPER APP CREDENTIALS
client_id = "8ad10722bf9f4c539591db26b5ae4abc" # Spotify developer app id
client_secret = "b978797c68c7425bb43ae4fbc238399e" # Spotify developer app password
# end of SPOTIFY DEVELOPER APP CREDENTIALS

app = Flask(__name__)

app.secret_key = "awienwbga48we5"
app.config['SESSION_COOKIE_NAME'] = 'cookie'

# Below is code to get user authorization using the Spotify 'Authorization Code Flow'.

# WITHOUT USING SPOTIPY LIBRARY

# Get user authorization
@app.route('/login')
def login():
    authorization_url = SPOTIFY_AUTH_URL + urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'scope': 'user-read-private user-read-email user-read-currently-playing user-library-read user-follow-read',
        'redirect_uri': url_for('callback', _external=True)
    })
    return redirect(authorization_url)

# Callback from authorization
@app.route('/callback')
def callback():
    # *1 -> This redirect_uri needs to be the same as the redirect_uri supplied 
    # when requesting the authorization code above (there's no actual redirection, it's used for validation only). 
    code = request.args.get('code')

    if code:
        request_data = {
            'code': code,
            'redirect_uri': url_for('callback', _external=True), # *1
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(SPOTIFY_ACCESS_TOKEN_URL, data=request_data).json()
        session['token_info'] = response

    # THIS IS JUST TO GET ACCESS TOKEN FOR ACCESSING NON-USER DATA (for this, we don't need code to get the access token)
    # response = requests.post(SPOTIFY_ACCESS_TOKEN_URL, {
    #     'grant_type': 'client_credentials',
    #     'client_id': client_id,
    #     'client_secret': client_secret,
    # })
    # response_json = response.json()
    # end of GET ACCESS TOKEN FOR ACCESSING NON-USER DATA

    return redirect('/')

# Get user's currently playing track using Python requests
@app.route('/current-track')
def get_current_track():
    # try:
    #     token_info = get_token()
    #     access_token = token_info['access_token']
    # except:
    #     print("user not logged in")
    #     return redirect("/")
    access_token = session['token_info']['access_token']

    response = requests.get(
        SPOTIFY_GET_CURRENT_TRACK_URL,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if response.status_code == 200:
        json_resp = response.json()

        track_id = json_resp['item']['id']
        track_name = json_resp['item']['name']
        artists = [artist for artist in json_resp['item']['artists']]

        link = json_resp['item']['external_urls']['spotify']

        artist_names = ', '.join([artist['name'] for artist in artists])

        current_track_info = {
            "id": track_id,
            "track_name": track_name,
            "artists": artist_names,
            "link": link
        }
        return current_track_info
    return {
            "id": '',
            "track_name": '',
            "artists": '',
            "link": ''
        }

# Get user's account information using Python requests
@app.route('/user-profile')
def get_user_profile():
    # try:
    #     token_info = get_token()
    #     access_token = token_info['access_token']
    # except:
    #     print("user not logged in")
    #     return redirect("/")
    access_token = session['token_info']['access_token']

    response = requests.get(
        SPOTIFY_GET_USER_PROFILE_URL,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    print(response)
    if response.status_code < 400:
        json_resp = response.json()
        return json_resp
    return ('User not found')

# Home page
@app.route('/')
def welcome():
    return 'Welcome Home!'

# end of WITHOUT USING SPOTIPY LIBRARY

# USING SPOTIPY LIBRARY

# Get user authorization
# @app.route('/login')
# def login():
#     spotify_oauth = create_spotify_oauth()
#     auth_url = spotify_oauth.get_authorize_url()
#     return redirect(auth_url)

# Callback from authorization
# @app.route('/callback')
# def callback():
#     spotify_oauth = create_spotify_oauth()
#     code = request.args.get('code')
#     token_info = spotify_oauth.get_access_token(code)
#     session['token_info'] = token_info
#     return redirect("/")

# Get user's currently playing track using Spotipy built in method
# @app.route('/spotipy-current-track')
# def spotipy_current_track():
#     sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
#             client_id=client_id,
#             client_secret=client_secret,
#             redirect_uri=url_for('welcome', _external=True),
#             scope='user-read-currently-playing'
#         ))

#     response = sp.current_user_playing_track()
#     if response:
#         json_resp = response

#         track_id = json_resp['item']['id']
#         track_name = json_resp['item']['name']
#         artists = [artist for artist in json_resp['item']['artists']]

#         link = json_resp['item']['external_urls']['spotify']

#         artist_names = ', '.join([artist['name'] for artist in artists])

#         current_track_info = {
#             "id": track_id,
#             "track_name": track_name,
#             "artists": artist_names,
#             "link": link
#         }
#         return current_track_info
#     return {
#             "id": '',
#             "track_name": '',
#             "artists": '',
#             "link": ''
#         }

# Get user's account information using Spotipy built in method
# @app.route('/spotipy-me')
# def spotipy_current_user():
#     sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
#             client_id=client_id,
#             client_secret=client_secret,
#             redirect_uri=url_for('welcome', _external=True),
#             scope="user-read-private user-read-email user-read-currently-playing user-library-read user-follow-read"
#         ))

#     result = sp.current_user()
#     return result

# def get_token():
#     # check if there's token data
#     token_info = session.get("token_info", None)
#     if not token_info:
#         raise "exception"

#     # check if the token has expired
#     time_now = int(time.time())
#     token_is_expired = token_info['expires_at'] - time_now < 60
#     if token_is_expired:
#         spotify_oauth = create_spotify_oauth()
#         token_info = spotify_oauth.get_refreshed_access_token(token_info['refresh_token'])
#     return token_info

# def create_spotify_oauth():
#     return SpotifyOAuth(
#         client_id=client_id,
#         client_secret=client_secret,
#         redirect_uri=url_for('callback', _external=True),
#         scope="user-read-private user-read-email user-read-currently-playing user-library-read user-follow-read"
#     )

# end of USING SPOTIPY LIBRARY

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5001)