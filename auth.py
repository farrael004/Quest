# Credit https://github.com/Sven-Bo/streamlit-sales-dashboard-with-userauthentication-database

import streamlit as st
import database as db
from datetime import datetime, timedelta
import streamlit_authenticator as stauth
from utils import tell_to_reload_page


class LoginSignup(stauth.Authenticate):
    def login(self, form_name):
        
        if not st.session_state['authentication_status']:
            self.token = self.cookie_manager.get(self.cookie_name)
            if self.token is not None:
                self.token = self.token_decode()
                if self.token is not False:
                    if not st.session_state['logout']:
                        if self.token['exp_date'] > datetime.utcnow().timestamp():
                            if 'name' and 'username' in self.token:
                                st.session_state['name'] = self.token['name']
                                st.session_state['username'] = self.token['username']
                                st.session_state['authentication_status'] = True

            if st.session_state['authentication_status'] != True:
                login, signup = st.tabs(['Login', 'Signup'])
                
                with login:
                    login_form = st.form('Login')
                    login_form.subheader(form_name)
                    self.username = login_form.text_input('Username')
                    st.session_state['username'] = self.username
                    self.password = login_form.text_input('Password', type='password')
                    remember = st.checkbox("Remember me")

                    if login_form.form_submit_button('Login'):
                        if remember: self.cookie_expiry_days = 30
                        self.index = None
                        for i in range(0, len(self.usernames)):
                            if self.usernames[i] == self.username:
                                self.index = i
                        if self.index is not None:
                            try:
                                if self.check_pw():
                                    st.session_state['name'] = self.names[self.index]
                                    self.exp_date = self.exp_date()
                                    self.token = self.token_encode()
                                    self.cookie_manager.set(self.cookie_name, self.token,
                                    expires_at=datetime.now() + timedelta(days=self.cookie_expiry_days))
                                    st.session_state['authentication_status'] = True
                                else:
                                    st.session_state['authentication_status'] = False
                            except Exception as e:
                                print(e)
                        else:
                            st.session_state['authentication_status'] = False
                            
                with signup:
                    with st.form('Signup'):
                        st.subheader('Signup')
                        name = st.text_input('Name')
                        username = st.text_input('Username')
                        password = st.text_input('Password', type='password')
                        confirm_password = st.text_input('Confirm password', type='password')
                        signup_button = st.form_submit_button('Signup')
                        
                    if signup_button:
                        if username in self.usernames:
                            st.warning('This username already exists. Please choose an unique username.')
                            st.stop()
                        
                        if name == '' or username == '' or password == '':
                            st.warning('Please fill all fields')
                            st.stop()
                        
                        if username == '__removed__':
                            st.warning('Invalid username')
                            st.stop()
                            
                        if password != confirm_password:
                            st.warning("Password does not match 'Confirm password' field.")
                            st.stop()
                        
                        hashed_password = stauth.Hasher([password]).hash(password)

                        db.insert_user(username, name, hashed_password)
                            
                        st.success('Successful account creation. You may now use the Login tab.', icon='✅')

        return st.session_state['name'], st.session_state['authentication_status'], st.session_state['username']
            
    def logout_function(self):
        self.cookie_manager.delete(self.cookie_name)
        st.session_state['logout'] = True
        st.session_state['name'] = None
        st.session_state['username'] = None
        st.session_state['authentication_status'] = None
        
        if 'api_key' in st.session_state:
            st.session_state.pop('api_key')
        if 'conversation' in st.session_state:
            st.session_state.pop('conversation')
        if 'google_history' in st.session_state:
            st.session_state.pop('google_history')
        if 'settings' in st.session_state:
            st.session_state.pop('settings')
        
        
    def logout_button(self, button_name):
        if st.button(button_name):
            self.logout_function()
            st.stop()

def authenticate_user():
    users = db.fetch_all_users()

    usernames = [user["key"] for user in users]
    names = [user["name"] for user in users]
    hashed_passwords = [user["password"] for user in users]

    authenticator = LoginSignup(names, usernames, hashed_passwords,
        "query_aichat", "abcdef", cookie_expiry_days=0)
    
    st.session_state['authenticator'] = authenticator
    
    (st.session_state['name'],
        authentication_status,
        st.session_state['username']) = authenticator.login("Login")
    
    if authentication_status == None:
        st.stop()
    if authentication_status == False:
            st.warning("Username/password is incorrect")
            st.stop()
        
def logout_button():
    st.session_state['authenticator'].logout_button("Logout")