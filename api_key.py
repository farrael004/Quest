import streamlit as st
import database as db
from utils import tell_to_reload_page
from gpt_api import test_api_key

# Load the API key to the session state
def load_api_key():
    if 'api_key' not in st.session_state:
        try:
            #api_key = db.get_api_key(st.session_state['username'])
            #st.session_state['api_key'] = api_key
            raise
        except:
            api_key_form()
    return st.session_state['api_key']


def api_key_form():
    with st.form('API Key'):
        api_key = st.text_input(label='Insert your API key here', type='password')
        api_submitted = st.form_submit_button("Submit")
        save_api_key = st.checkbox('Remember my key.',disabled=True)

    st.markdown("[Find your API key here](https://beta.openai.com/account/api-keys)")
    
    if api_submitted:
        test_api_key(api_key)
    
    # Associate the user API key with the user account   
    if api_submitted and save_api_key:
        db.insert_api_key(st.session_state['username'], api_key)

    if api_submitted:
        st.session_state['api_key'] = api_key
        st.experimental_rerun()
        
    st.stop()

def reset_api_key():
    #db.delete_api_key(st.session_state['username'])
    if 'api_key' in st.session_state:
        st.session_state.pop('api_key')
    st.experimental_rerun()

def reset_key_button():
    st.button('Reset API Key', on_click=reset_api_key)
        