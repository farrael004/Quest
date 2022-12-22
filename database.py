# Credit https://github.com/Sven-Bo/streamlit-sales-dashboard-with-userauthentication-database

from cryptography.fernet import Fernet
import streamlit as st
import json
import datetime
from deta import Deta  # pip install deta


DETA_KEY = st.secrets["DETA_KEY"]
KEY_MAP = bytes(st.secrets['KEY_MAP'], "utf-8")

deta = Deta(DETA_KEY)
cipher = Fernet(KEY_MAP)


def encrypt(data):
    if type(data) != bytes: data = string_to_bytes(data) 
    return bytes_to_string(cipher.encrypt(data))


def decrypt(data):
    if type(data) != bytes: data = string_to_bytes(data) 
    return bytes_to_string(cipher.decrypt(data))


def string_to_bytes(string: str):
    return string.encode('utf-8')


def bytes_to_string(bytes: bytes):
    return bytes.decode("utf-8")


db = deta.Base("quest_users")
db_api_key = deta.Base("quest_api_key")
db_search_history = deta.Base("quest_search_history")

def insert_user(username, name, password):
    """Returns the user on a successful user creation, otherwise raises and error"""
    return db.put({"key": username, "name": name, "password": password})


def fetch_all_users():
    """Returns a dict of all users"""
    res = db.fetch()
    return res.items

def get_user(username):
    """If not found, the function will return None"""
    return db.get(username)


def update_user(username, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    return db.update(updates, username)


def delete_user(username):
    """Always returns None, even if the key does not exist"""
    return db.delete(username)


def insert_api_key(username, api_key):
    now = datetime.datetime.now()
    thirty_days_from_now = now + datetime.timedelta(days=30)
    try: # If key exists in the database
        get_api_key(username)
        return db_api_key.update({'api_key': encrypt(api_key)}, username, expire_in=thirty_days_from_now)
    except TypeError: # If key doesn't exist in the database
        return db_api_key.put({'key': username, 'api_key': encrypt(api_key)}, expire_in=thirty_days_from_now)


def get_api_key(username):
    encrypted_key = db_api_key.get(username)['api_key']
    return decrypt(encrypted_key)


def delete_api_key(username):
    return db_api_key.delete(username)


def insert_search_history(username, search_entry):
    search_entry['username'] = username
    try: # In the rare chance two random strings are used at the same time, try again with a different string
        return db_search_history.put(search_entry)
    except:
        return db_search_history.put(search_entry)


def get_user_search_history(username):
    entries = db_search_history.fetch({'username': username}).items
    history = [entry.drop('username') for entry in entries]
    print(history)
    return history


def delete_search_history(username):
    user_history_keys = db_search_history.fetch({'username': username}).items['key']
    for key in user_history_keys:
        db_search_history.delete(key)