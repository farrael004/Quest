# Credit https://github.com/Sven-Bo/streamlit-sales-dashboard-with-userauthentication-database

from cryptography.fernet import Fernet
import streamlit as st
import pandas as pd
import datetime
from deta import Deta  # pip install deta
from utils import tell_to_reload_page


#DETA_KEY = st.secrets["DETA_KEY"]
#KEY_MAP = bytes(st.secrets['KEY_MAP'], "utf-8")

#deta = Deta(DETA_KEY)
#cipher = Fernet(KEY_MAP)


#def encrypt(data):
#    if type(data) != bytes: data = string_to_bytes(data) 
#    return bytes_to_string(cipher.encrypt(data))


#def decrypt(data):
#    if type(data) != bytes: data = string_to_bytes(data) 
#    return bytes_to_string(cipher.decrypt(data))


def string_to_bytes(string: str):
    return string.encode('utf-8')


def bytes_to_string(bytes: bytes):
    return bytes.decode("utf-8")


#db_login = deta.Base("quest_users")
#db_api_key = deta.Base("quest_api_key")
#db_search_history = deta.Base("quest_internet_search")
#db_user_settings = deta.Base("quest_user_settings")


def insert_user(username, name, password):
    """Returns the user on a successful user creation, otherwise raises and error"""
    #return db_login.put({"key": username, "name": name, "password": password})


def fetch_all_users():
    """Returns a dict of all users"""
    #res = db_login.fetch()
    #return res.items

def get_user(username):
    """If not found, the function will return None"""
    #return db_login.get(username)


def update_user(username, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    #return db_login.update(updates, username)


def delete_user_login(username):
    """Always returns None, even if the key does not exist"""
    st.session_state['authenticator'].logout_function()
    #db_login.delete(username)
    #tell_to_reload_page()


def insert_api_key(username, api_key):
    now = datetime.datetime.now()
    thirty_days_from_now = now + datetime.timedelta(days=1)
    #try: # If key exists in the database
        #get_api_key(username)
        #return db_api_key.update({'api_key': encrypt(api_key)}, username, expire_at=thirty_days_from_now)
    #except TypeError: # If key doesn't exist in the database
        #return db_api_key.put({'key': username, 'api_key': encrypt(api_key)}, expire_at=thirty_days_from_now)


def get_api_key(username):
    #encrypted_key = db_api_key.get(username)['api_key']
    #return decrypt(encrypted_key)
    raise


def delete_api_key(username):
    #return db_api_key.delete(username)
    pass


def insert_search_history(search_entry):
    #return db_search_history.put_many(search_entry)
    pass


def get_user_search_history(username):
    #if username == '__removed__': return []
    #entries = db_search_history.fetch({'username': username}).items
    #return entries
    raise


def delete_search_history(username):
    #user_history = db_search_history.fetch({'username': username}).items
    #user_history = pd.DataFrame(user_history)
    #if user_history.empty: return
    #with st.spinner("Deleting search history."):
        #for key in user_history['key']:
            #db_search_history.update({'username': '__removed__'}, key=key)
        #st.session_state.pop('google_history', None)
    pass
        
        
def delete_user_data(username):
    delete_search_history(username)
    delete_api_key(username)
    delete_user_login(username)
    
def delete_user_button():
    with st.form("Delete all user data."):
        st.write('Delete all user data')
        st.warning("This will permanently delete all of your data \
            with no chance for recovery.")
        confirmation = st.text_input('Type "delete me"')
        submit_button = st.form_submit_button("Submit")
        if submit_button:
            if confirmation == 'delete me':
                delete_user_data(st.session_state['username'])