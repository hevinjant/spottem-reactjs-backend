#pylint: disable=C0301
#pylint: disable=R0903
#pylint: disable=R0913
#pylint: disable=W0105
#pylint: disable=W0107

""" Database manager for Spottem """

import pymongo
from pymongo import MongoClient
import certifi

mongodb_user_pass = "UZUtNpo3GhKSnYaG"
mongodb_connection_string = "mongodb+srv://hevj:" + mongodb_user_pass + "@cluster0.1rgh3.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

class User:
    """ Class to store user's information """
    def __init__(self,display_name, user_id, email, user_pic):
        self.display_name = display_name
        self.user_id = user_id
        self.email = email
        self.is_online = False
        self.user_pic = user_pic
        self.friends = []
        self.song_history = []

class Song:
    """ Class to store song's information """
    def __init__(self, track_id, track_name, artists, time_stamp, track_url, album_pic):
        self.track_id = track_id
        self.track_name = track_name
        self.artists = artists
        self.time_stamp = time_stamp
        self.track_url = track_url
        self.reactions = []
        self.album_pic = album_pic

class Reaction:
    """ Class to store reaction's information """
    def __init__(self, reaction_type, sender, time_stamp):
        self.reaction_type = reaction_type
        self.sender = sender
        self.time_stamp = time_stamp

class Database:
    """ Database manager to perform CRUD to MongoDB """
    cluster = MongoClient(mongodb_connection_string, tlsCAFile=certifi.where())
    db = cluster['spottem-db']
    collection = db['user']

    def insert_user(self, new_user):
        """ Insert the given User object to the database collection """
        self.collection.insert_one(new_user.__dict__)

    def get_user(self, user_email):
        """ Get the user data of the given user email """
        query = {
            'email': user_email
        }
        user = self.collection.find_one(query)
        return user

    def remove_user(self, user_email):
        """ Remove user from the database """
        query = {
            'email': user_email
        }
        self.collection.delete_one(query)

    def user_exists(self, user_email):
        """ Return true if user has existed in the database """
        query = {
            'email': user_email
        }
        result = self.collection.count_documents(query)
        return result == 1

    def insert_song_for_user(self, user_email, song):
        """ Insert a Song object to the user's song history array """
        query = {
            'email': user_email
        }
        self.collection.update_one(
            query,
            {   
                # Note: $set is to update a specific field of the entry.
                #       $push is to append to a specific field of the entry.
                '$push': {'song_history': song.__dict__}
            }
        )

    def insert_reaction_for_user_song(self, user_email, track_id, reaction):
        """ Insert Reaction object to a user's song"""
        query = {
            'email': user_email,
            'song_history.track_id': track_id
        }
        self.collection.update_one(
            query,
            {   
                '$push': {'song_history.$.reactions': reaction.__dict__}
            }
        )

    def get_reactions_for_user_song(self, user_email, track_id):
        """ Get all the reactions of a user's song by the given track id """
        reactions = []
        user = self.get_user(user_email)
        for song in user['song_history']:
            if song['track_id'] == track_id:
                for reaction in song['reactions']:
                    reactions.append(reaction)
        return reactions
