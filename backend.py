#pylint: disable=R0903
#pylint: disable=R0913
#pylint: disable=W0105
#pylint: disable=W0107

""" The module below is to get user authorization using the Spotify 'Authorization Code Flow' """

import requests
from flask import Flask, request, url_for, session, jsonify, redirect, render_template
from urllib.parse import urlencode
from database_manager2 import User, Song, Reaction, Database, get_converted_email, get_original_email
import uuid
import os

class AccessTokenError(Exception):
    """ Custom exception for when access token is not found """
    pass

# URI FOR GCP: https://spottem.wl.r.appspot.com/callback

# SPOTIFY END POINTS
"""
Url where user is asked to login and to give permission.
We redirect user to this url and also provide the required information to Spotify,
we then get a code in return from Spotify.
We can grab the code from the argument of our callback url.
"""
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize?'

"""
Url where we can get the token info by providing the code.
Using the code that we got by requesting to the above url as one of the parameters,
we can get the token info from Spotify.
Token info consists of the access token, the expiration time, and the refresh token.
"""
SPOTIFY_ACCESS_TOKEN_URL = 'https://accounts.spotify.com/api/token'

""" End point url to get user current track """
SPOTIFY_GET_CURRENT_TRACK_URL = 'https://api.spotify.com/v1/me/player/currently-playing'

""" End point url to get user account information """
SPOTIFY_GET_USER_PROFILE_URL = 'https://api.spotify.com/v1/me'
# end of SPOTIFY END POINTS

# SPOTIFY DEVELOPER APP CREDENTIALS
#CLIENT_ID = os.environ.get('CLIENT_ID') # Spotify developer app id
#CLIENT_SECRET = os.environ.get('CLIENT_SECRET') # Spotify developer app password
# end of SPOTIFY DEVELOPER APP CREDENTIALS

#app = Flask(__name__)

#app.secret_key = os.environ.get('APP_SECRET_KEY')
#app.config['SESSION_COOKIE_NAME'] = 'cookie'

#####
# SPOTIFY DEVELOPER APP CREDENTIALS
CLIENT_ID = "8ad10722bf9f4c539591db26b5ae4abc" # Spotify developer app id
CLIENT_SECRET = "b978797c68c7425bb43ae4fbc238399e" # Spotify developer app password
# end of SPOTIFY DEVELOPER APP CREDENTIALS

app = Flask(__name__)

app.secret_key = "awienwbga48we5"
app.config['SESSION_COOKIE_NAME'] = 'cookie'
#####


# End point to get user authorization
@app.route('/login')
def login():
    """ Returns the Spotify authorization url with the parameters included """
    authorization_url = SPOTIFY_AUTH_URL + urlencode({
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': 'user-read-private user-read-email user-read-currently-playing user-library-read',
        'redirect_uri': 'http://localhost:5001/callback'
    })
    return jsonify({'oauth_url': authorization_url}), 200

# End point for the callback from authorization
@app.route('/callback')
def callback():
    """ Gets token info by providing the Spotify code and return 200 if successful """
    # *1 -> This redirect_uri needs to be the same as the redirect_uri supplied
    # when requesting the authorization code above
    # (there's no actual redirection, it's used for validation only).

    code = request.args.get('code')

    if code:
        request_data = {
            'code': code,
            'redirect_uri': 'http://localhost:5001/callback', # *1
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(SPOTIFY_ACCESS_TOKEN_URL, data=request_data).json()
        session['token_info'] = response

        # insert user to database
        user_data = get_user_spotify_data()
        insert_user_to_database(user_data)
        session['logged_user'] = get_converted_email(user_data['email'])

        return redirect('http://localhost:3000/home')
    return jsonify({"success":"False"}), 400

# End point to get user's currently playing track using Python requests, and insert it to the database
@app.route('/current-track/<email>')
def get_current_track(email):
    """ Returns the current playing track of a user, access token is needed """
    #logged_user = session['logged_user']
    response = get_user_current_track()
    if response:
        # insert the current track to the logged in user's database
        song = Song(email, response['id'], response['track_name'], response['artists'], "", response['link'], response['image_url'])
        Database().update_current_track(email, song)
        return response
    Database().update_current_track(email, None)
    return jsonify({"error":"there is no track playing."}), 404

# End point to get user's currently playing track using Python requests
@app.route('/current-track/spotify')
def get_current_track_spotify():
    """ Returns the current playing track of a user, access token is needed """
    logged_user = session['logged_user']
    response = get_user_current_track()
    if response:
        return response
    return jsonify({"error":"there is no track playing."}), 404

# End point to get user's Spotify account information using Python requests
@app.route('/user-profile')
def get_user_profile():
    """ Returns the Spotify account information of a user, access token is needed """
    response = get_user_spotify_data()
    if response:
        return response
    return jsonify({"error":"User not found"}), 404

# End point of the home page
@app.route('/')
def welcome():
    """ Home page of the backend """
    return 'Welcome Home!'

# Get user from database
# @app.route('/user/<email>')
# def get_user_from_db(email):
#     if Database().user_exists(email):
#         user_data = Database().get_user(email)
#         return jsonify({'user': user_data}), 200
#     return jsonify({"error":"User not found"}), 404

# Get complete user information from database (including songs and reactions)
@app.route('/user/<email>')
def get_user_from_db(email):
    """ Get user from database """
    if Database().user_exists(email):
        user = get_complete_user_info(email)
        if user:
            # # also get the current playing track if the <email> is the current logged in user
            # if user['email'] == session['logged_user']:
            #     current_track = get_user_current_track()
            #     user['current_track'] = current_track
            return jsonify({'user': user}), 200
    return jsonify({"error":"User not found"}), 404

# Get all friends or insert a friend for a user
@app.route('/user/friends/<email>', methods=['GET', 'POST', 'DELETE'])
def get_or_insert_friend_for_user(email):
    if request.method == 'GET':
        if Database().user_exists(email):
            result = []
            friends = Database().get_all_user_friends(email)
            for friend in friends:
                friend_data = get_complete_user_info(friend)
                result.append(friend_data)
            return jsonify({'friends': result}), 200
        return jsonify({"error":"User not found"}), 404
    elif request.method == 'POST':
        new_friend_json = request.get_json()
        success = Database().insert_friend_to_user(new_friend_json['email'], new_friend_json['friend_email'])
        if success:
            return jsonify({'new_friend': new_friend_json}), 201
        return jsonify({'new_friend': new_friend_json}), 204
    elif request.method == 'DELETE':
        remove_friend_json = request.get_json()
        if Database().user_exists(email):
            Database().delete_friend(remove_friend_json['email'], remove_friend_json['friend_email'])
            response = jsonify(success=True)
            response.status_code = 204
            return response

# Get or insert song history for user
@app.route('/songs/<email>', methods=['GET','POST'])
def get_or_insert_song_history_from_db(email):
    if request.method == 'GET':
        if Database().song_history_for_user_exists(email):
            song_history = Database().get_all_song_history_from_user(email)
            return jsonify({'song_history': song_history}), 200
        return jsonify({"error":"song history not found"}), 404
    elif request.method == 'POST':
        song_history_json = request.get_json()
        song_history = Song(song_history_json['email'], song_history_json['song_id'], song_history_json['song_name'], song_history_json['song_artists'], song_history_json['song_album'], song_history_json['song_url'], song_history_json['song_image_url'])
        Database().create_song_history(song_history)
        return jsonify({'song_history':song_history_json}), 201

# Get and Insert reaction for a song to database
@app.route('/reactions/<email>/<song_id>', methods=['GET', 'POST'])
def get_or_insert_reactions_from_db(email, song_id):
    if request.method == 'GET':
        if Database().reaction_exists(email, song_id):
            reactions = Database().get_reactions(email, song_id)
            return jsonify({'reactions': reactions}), 200
        return jsonify({"error":"reactions not found"}), 404
    elif request.method == 'POST':
        reaction_json = request.get_json()
        name = Database().get_user(reaction_json['email'])
        name = name['name']
        sender_name = Database().get_user(reaction_json['sender_email'])
        sender_name = sender_name['name']
        reaction = Reaction(reaction_json['email'], name, reaction_json['sender_email'], sender_name, reaction_json['song_id'], reaction_json['song_name'], reaction_json['song_artist'], reaction_json['song_album'], reaction_json['song_url'], reaction_json['song_image_url'], reaction_json['time_stamp'])
        Database().create_reaction(reaction)
        return jsonify({'reaction':reaction_json}), 201

# Get all reactions for all users
@app.route('/reactions')
def get_all_reactions():
    reactions = Database().get_all_reactions()
    return jsonify({'reactions':reactions}), 201

# Insert new user to the database
def insert_user_to_database(user_data):
    """ Check if user has existed in the database, if not insert the user to the database """
    if user_data:
        user_email = user_data['email']
        user_display_name = user_data['display_name']
        user_id = user_data['id']
        user_pic = user_data['images'][0]['url']
        if not Database().user_exists(user_email):
            new_user = User(user_display_name, user_id, user_email, user_pic)
            Database().create_user(new_user)

# Get complete user object
def get_complete_user_info(email):
    """ Get the complete user data including songs history, reactions, and current track """
    if Database().user_exists(email):
        user = Database().get_user(email)
        user['song_history'] = Database().get_all_song_history_from_user(email)
        for song in user['song_history']:
            reactions = Database().get_reactions(email, song['song_id'])
            song['reactions'] = reactions
        return user
    return None

# Get user's Spotify account information using Python requests
def get_user_spotify_data():
    """ Returns the Spotify account information of a user, access token is needed """
    try:
        access_token = session['token_info']['access_token']
    except AccessTokenError:
        print("cannot find access token")

    response = requests.get(
        SPOTIFY_GET_USER_PROFILE_URL,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if response.status_code < 400:
        json_resp = response.json()
        return json_resp
    return None

# Get user's currently playing track using Python requests
def get_user_current_track():
    """ Returns the current playing track of a user, access token is needed """
    try:
        access_token = session['token_info']['access_token']
    except AccessTokenError:
        print("cannot find access token")

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
        artists = list(json_resp['item']['artists'])
        image_url = json_resp['item']['album']['images'][0]['url']

        link = json_resp['item']['external_urls']['spotify']

        artist_names = ', '.join([artist['name'] for artist in artists])

        current_track_info = {
            "id": track_id,
            "track_name": track_name,
            "artists": artist_names,
            "link": link,
            "image_url": image_url
        }
 
        return current_track_info
    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
