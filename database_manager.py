from pymongo import MongoClient
import certifi
import os

DB_ENDPOINT = os.environ.get('DB_ENDPOINT')


def get_converted_email(email):
    converted = email.replace('.', '-')
    return converted


def get_original_email(email):
    converted = email.replace('-', '.')
    return converted

# class user to store user data


class User:
    """ Class to store user data """

    def __init__(self, name, user_id, email, user_dp):
        self.name = name
        self.user_id = user_id
        self.email = get_converted_email(email)
        self.user_dp = user_dp
        self.is_online = False
        self.friends = []
        self.current_track = None

# class to store song data


class Song:
    """ Class to store song data """

    def __init__(self, email, song_id, song_name, artist, album, song_url, song_image_url, preview_url):
        self.email = get_converted_email(email)
        self.song_id = song_id
        self.song_name = song_name
        self.artist = artist
        self.album = album
        self.song_url = song_url
        self.song_image_url = song_image_url
        self.preview_url = preview_url

# class to store reaction data


class Reaction:
    """ Class to store reaction data """

    def __init__(self, email, name, sender_email, sender_name, song_id, song_name, artist, album, song_url, song_image_url, preview_url, time_stamp):
        self.email = get_converted_email(email)
        self.name = name
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.song_id = song_id
        self.song_id = song_id
        self.song_name = song_name
        self.artist = artist
        self.album = album
        self.song_url = song_url
        self.song_image_url = song_image_url
        self.preview_url = preview_url
        self.time_stamp = time_stamp

# Database manager to perform CRUD operations on the database using the MongoDB driver


class Database:
    """ Database Manager to perform CRUD to MongoDB """

    def __init__(self):
        self.cluster = MongoClient(DB_ENDPOINT, tlsCAFile=certifi.where())
        self.db = self.cluster["spottem"]
        self.user_coll = self.db["user"]
        self.song_history_coll = self.db["song_history"]
        self.reactions_coll = self.db["reactions"]

    # USER CRUD OPERATIONS
    def create_user(self, user):
        """ Create a user in the database """
        self.user_coll.insert_one(user.__dict__)

    def get_user(self, user_email):
        """ Get a user from the database """
        query = {
            "email": get_converted_email(user_email)
        }
        user = self.user_coll.find_one(query)
        user['_id'] = str(user['_id'])
        return user

    def delete_user(self, user_email):
        """ Delete a user from the database """
        query = {
            "email": get_converted_email(user_email)
        }
        self.user_coll.delete_one(query)

    def user_exists(self, user_email):
        """ Check if a user exists in the database """
        query = {
            "email": get_converted_email(user_email)
        }
        return self.user_coll.find_one(query) is not None

    def insert_friend_to_user(self, user_email, friend_email):
        """ Insert a friend to user friends array """
        # check if friend_email is a valid user
        if not (self.user_exists(friend_email)):
            return False

        # check if friend already exists in the friend list
        existing_friends = self.get_all_user_friends(user_email)
        if get_original_email(friend_email) in existing_friends:
            return False

        query = {
            "email": get_converted_email(user_email)
        }
        self.user_coll.update_one(
            query,
            {
                "$push": {"friends": get_converted_email(friend_email)}
            }
        )
        return True

    def delete_friend(self, user_email, friend_email):
        user_email = get_converted_email(user_email)
        friend_email = get_converted_email(friend_email)
        user = self.get_user(user_email)
        if user:
            friends = user['friends']
            if friend_email in friends:
                friends.remove(friend_email)
            query = {
                "email": user_email
            }
            self.user_coll.update_one(
                query,
                {
                    "$set": {'friends': friends}
                }
            )

    def get_all_user_friends(self, user_email):
        """ Get all friends of a user """
        user = self.get_user(user_email)
        friends = []
        for friend in user["friends"]:
            friends.append(get_original_email(friend))
        return friends

    def update_current_track(self, user_email, song):
        """ Update the current playing track of user in the database """
        # get the current user's current track
        user = self.get_user(user_email)

        if song:
            # check if user has a current track playing
            if user['current_track']:
                # if the previous current track is different than the current track,
                # update the current track to the new one,
                # and move the previous current track to song history
                if user['current_track']['song_id'] != song.song_id:
                    query = {
                        "email": get_converted_email(user_email)
                    }
                    self.user_coll.update_one(
                        query,
                        {
                            "$set": {'current_track': song.__dict__}
                        }
                    )

                    prev_current_track = Song(user['current_track']['email'], user['current_track']['song_id'], user['current_track']['song_name'], user['current_track']['artist'],
                                              user['current_track']['album'], user['current_track']['song_url'], user['current_track']['song_image_url'], user['current_track']['preview_url'])
                    self.create_song_history(prev_current_track)
            else:
                query = {
                    "email": get_converted_email(user_email)
                }
                self.user_coll.update_one(
                    query,
                    {
                        "$set": {'current_track': song.__dict__}
                    }
                )
        else:
            query = {
                "email": get_converted_email(user_email)
            }
            self.user_coll.update_one(
                query,
                {
                    "$set": {'current_track': None}
                }
            )

    # SONG HISTORY CRUD OPERATIONS
    def create_song_history(self, song_history):
        """ Create a song history in the database """
        # check if the song history with the same user and song has already existed
        existing_song_history = self.get_all_song_history_from_user(
            song_history.email)
        for song in existing_song_history:
            if (song_history.song_id == song['song_id']):
                return

        self.song_history_coll.insert_one(song_history.__dict__)

    def get_all_song_history_from_user(self, user_email):
        """ Get a song history from the database """
        query = {
            "email": get_converted_email(user_email)
        }
        response = self.song_history_coll.find(query)
        songs = []
        for song in response:
            song['_id'] = str(song['_id'])
            songs.append(song)
        return songs

    def delete_all_song_history_for_user(self, user_email):
        """ Delete a song history from the database """
        query = {
            "email": get_converted_email(user_email)
        }
        self.song_history_coll.delete_many(query)

    def song_history_for_user_exists(self, user_email):
        """ Check if a song history exists in the database """
        query = {
            "email": get_converted_email(user_email)
        }
        return self.song_history_coll.find_one(query) is not None

    # REACTIONS CRUD OPERATIONS
    def create_reaction(self, reaction):
        """ Create a reaction in the database """
        reactions = self.get_all_reactions()
        for r in reactions:
            if r['song_id'] == reaction.song_id and r['email'] == reaction.email and r['sender_email'] == reaction.sender_email:
                return
        self.reactions_coll.insert_one(reaction.__dict__)

    def get_reactions(self, user_email, song_id):
        """ Get a reaction from the database for recipient """
        query = {
            "email": get_converted_email(user_email),
            "song_id": song_id
        }
        response = self.reactions_coll.find(query)
        reactions = []
        for reaction in response:
            reaction['_id'] = str(reaction['_id'])
            reactions.append(reaction)
        return reactions

    def get_sender_reactions(self, sender_email, song_id):
        """ Get a reaction from the database for sender """
        query = {
            "sender_email": get_converted_email(sender_email),
            "song_id": song_id
        }
        response = self.reactions_coll.find(query)
        reactions = []
        for reaction in response:
            reaction['_id'] = str(reaction['_id'])
            reactions.append(reaction)
        return reactions

    def get_all_reactions(self):
        """ Get all reactions from the Reactions collection """
        reactions = []
        response = self.reactions_coll.find()
        for reaction in response:
            reaction['_id'] = str(reaction['_id'])
            reactions.append(reaction)
        print(reactions)
        return reactions

    def delete_reaction(self, user_email, song_id):
        """ Delete a reaction from the database for recipient """
        query = {
            "email": get_converted_email(user_email),
            "song_id": song_id
        }
        self.reactions_coll.delete_one(query)

    def delete_sender_reaction(self, sender_email, song_id):
        """ Delete a reaction from the database for sender """
        query = {
            "sender_email": get_converted_email(sender_email),
            "song_id": song_id
        }
        self.reactions_coll.delete_one(query)

    def reaction_exists(self, user_email, song_id):
        """ Check if a reaction exists in the database """
        query = {
            "email": get_converted_email(user_email),
            "song_id": song_id
        }
        return self.reactions_coll.find_one(query) is not None

    def reaction_sender_exists(self, sender_email, song_id):
        """ Check if sender_email gives reaction to song_id """
        query = {
            "sender_email": get_converted_email(sender_email),
            "song_id": song_id
        }
        return self.reactions_coll.find_one(query) is not None


"""
# NEW USER JSON


# NEW SONG JSON
{
    "email": "hevin-jant@gmail-com",
    "song_id": "song id",
    "track_name": "song name",
    "artists": "song artists",
    "album": "album",
    "song_url": "song url",
    "image_url": "song image url"
}

# NEW REACTION JSON
{
    "email": "hevin-jant@gmail-com",
    "sender_email": "travisphawley@gmail-com",
    "song_id": "sid0",
    "song_name": "song name - 0",
    "song_artist": "song artist - 0",
    "song_album": "song album - 0",
    "song_url": "song url - 0",
    "song_image_url": "song image url - 0",
    "time_stamp": "11/27/2021"
}

# NEW FRIEND JSON
{
    "email": "hevin.jant@gmail.com",
    "friend_email": "newfriend@email.com"
}
"""
