import pytest
from database_manager import User, Song, Reaction, Database, get_converted_email, get_original_email

test_email = 'testuser@spottem.com'
converted_test_email = get_converted_email(test_email)
sender_email = get_converted_email('somerandom@gmail.com')

# UTIL TESTS


def test_convert_email():
    converted = get_converted_email(test_email)
    assert converted == 'testuser@spottem-com'


def test_convert_original_email():
    converted = get_converted_email(test_email)
    original = get_original_email(converted)
    assert original == test_email

# USER CRUD TESTS


def test_create_user():
    new_user = User('Test User', 0, test_email, None)
    Database().create_user(new_user)
    isExist = Database().user_exists(converted_test_email)
    assert isExist == True


def test_get_user():
    user = Database().get_user(converted_test_email)
    assert user['email'] == converted_test_email


def test_update_current_track():
    song = Song(test_email, 'abc123', 'Test Song', 'Test Artist',
                'Test Album', 'http://testurl.com', None)
    Database().update_current_track(converted_test_email, song)
    user = Database().get_user(converted_test_email)
    assert user['current_track']['song_id'] == 'abc123'


def test_update_current_track2():
    song = Song(test_email, 'abc456', 'Test Song', 'Test Artist',
                'Test Album', 'http://testurl.com', None)
    Database().update_current_track(converted_test_email, song)
    user = Database().get_user(converted_test_email)
    assert user['current_track']['song_id'] == 'abc456'


def test_update_current_track3():
    Database().update_current_track(converted_test_email, None)
    user = Database().get_user(converted_test_email)
    assert user['current_track'] == None


def test_insert_friend():
    new_friend = 'newfriend@test-com'
    Database().insert_friend_to_user(converted_test_email, new_friend)
    friends = Database().get_all_user_friends(converted_test_email)
    isExist = get_original_email(new_friend) in friends
    assert isExist == True


def test_insert_friend2():
    new_friend = 'newfriend@test-com'
    Database().insert_friend_to_user(converted_test_email, new_friend)
    friends = Database().get_all_user_friends(converted_test_email)
    assert len(friends) == 1


def test_delete_friend():
    new_friend = 'newfriend@test-com'
    Database().delete_friend(converted_test_email, new_friend)
    friends = Database().get_all_user_friends(converted_test_email)
    assert len(friends) == 0


def test_delete_user():
    Database().delete_user(test_email)
    isExist = Database().user_exists(converted_test_email)
    assert isExist == False

# SONG HISTORY CRUD TESTS


def test_create_song_history():
    song_history = Song(test_email, 'abc123', 'Test Song',
                        'Test Artist', 'Test Album', 'http://testurl.com', None)
    Database().create_song_history(song_history)
    isExist = Database().song_history_for_user_exists(converted_test_email)
    assert isExist == True


def test_get_all_song_history():
    song_history = Database().get_all_song_history_from_user(converted_test_email)
    assert song_history[0]['song_name'] == 'Test Song'


def test_delete_all_song_history():
    Database().delete_all_song_history_for_user(converted_test_email)
    isExist = Database().song_history_for_user_exists(converted_test_email)
    assert isExist == False

# REACTION CRUD TESTS


def test_create_reaction():
    song_history = Song(test_email, 'song123', 'Test Song',
                        'Test Artist', 'Test Album', 'http://testurl.com', None)
    Database().create_song_history(song_history)
    reaction = Reaction(converted_test_email, 'name', sender_email, 'sender name', 'song123',
                        'song name', 'song artists', 'song album', 'song url', 'song image url', 'time stamp')
    Database().create_reaction(reaction)
    isExist = Database().reaction_exists(converted_test_email, 'song123')
    assert isExist == True


def test_create_reaction2():
    reaction = Reaction(converted_test_email, 'name', sender_email, 'sender name', 'song123',
                        'song name', 'song artists', 'song album', 'song url', 'song image url', 'time stamp')
    Database().create_reaction(reaction)
    reactions = Database().get_all_reactions()
    count = 0
    for r in reactions:
        if r['song_id'] == reaction.song_id:
            count += 1
    assert count == 1


def test_get_reaction():
    reactions = Database().get_reactions(converted_test_email, 'song123')
    assert reactions[0]['song_id'] == 'song123'


def test_get_all_reactions():
    reactions = Database().get_all_reactions()
    isExist = False
    for reaction in reactions:
        if reaction['song_id'] == 'song123':
            isExist = True
    assert isExist == True


def test_delete_reaction():
    Database().delete_reaction(converted_test_email, 'song123')
    isExist = Database().reaction_exists(converted_test_email, 'song123')
    assert isExist == False
