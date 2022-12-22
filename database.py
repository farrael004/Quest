# Credit https://github.com/Sven-Bo/streamlit-sales-dashboard-with-userauthentication-database

from cryptography.fernet import Fernet
import streamlit as st
import json
import pandas as pd
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


db_login = deta.Base("quest_users")
db_api_key = deta.Base("quest_api_key")
#db_search_history = deta.Base("quest_search_history")
db_search_history = deta.Base("quest_internet_search")
db_user_settings = deta.Base("quest_user_settings")


def insert_user(username, name, password):
    """Returns the user on a successful user creation, otherwise raises and error"""
    return db_login.put({"key": username, "name": name, "password": password})


def fetch_all_users():
    """Returns a dict of all users"""
    res = db_login.fetch()
    return res.items

def get_user(username):
    """If not found, the function will return None"""
    return db_login.get(username)


def update_user(username, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    return db_login.update(updates, username)


def delete_user_login(username):
    """Always returns None, even if the key does not exist"""
    return db_login.delete(username)


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


def insert_search_history(search_entry):
    return db_search_history.put_many(search_entry)
    #return db_search_history.put({'A': 1, 'B': 2})


def get_user_search_history(username):
    if username == '__removed__': return []
    entries = db_search_history.fetch({'username': username}).items
    return entries


def delete_search_history(username):
    user_history_keys = db_search_history.fetch({'username': username}).items['key']
    for key in user_history_keys:
        db_search_history.update({'username': '__removed__'}, key=key)
        
        
def delete_user_data(username):
    delete_user_login(username)
    delete_api_key(username)
    delete_search_history(username)
    
def delete_user_button():
    with st.form('button'):
        delete_user = st.form_submit_button("Delete all user data")
    if delete_user:
        with st.container():
            st.warning("This will permanently delete all of your data \
                with no chance for recovery.")
            confirmation = st.text_input('Type "delete me"')
            if confirmation == 'delete me':
                delete_user_data(st.session_state['username'])
    