import streamlit as st
import database as db

# Load the API key to the session state
def load_api_key():
    if 'api_key' not in st.session_state:
        try:
            api_key = db.get_api_key(st.session_state['username'])
            st.session_state['api_key'] = api_key
        except:
            api_key_form()

            
    return st.session_state['api_key']


def api_key_form():
    with st.form('API Key'):
        api_key = st.text_input(label='Insert your API key here', type='password')
        api_submitted = st.form_submit_button("Submit")
        save_api_key = st.checkbox('Remember my key.')

    st.markdown("[Find your API key here](https://beta.openai.com/account/api-keys)")
    
    # Associate the user API key with the user account   
    if api_submitted and save_api_key:
        db.insert_api_key(st.session_state['username'], api_key)

    if api_submitted:
        st.session_state['api_key'] = api_key
        st.experimental_rerun()
        
    st.stop()

def reset_api_key():
    db.delete_api_key(st.session_state['username'])
    api_key_form()

def reset_key_button():
    st.button('Reset API Key', on_click=reset_api_key)
        