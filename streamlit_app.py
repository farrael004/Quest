import streamlit as st
from streamlit_extras.buy_me_a_coffee import button
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.badges import badge
from streamlit_lottie import st_lottie
import openai
from utils import load_lottie_url
from api_key import load_api_key, reset_key_button
from internet_search import *
from assistant import *
from gpt_api import find_top_similar_results
from auth import authenticate_user, logout_button


st.set_page_config(page_title='Quest🔍')
st.title("Quest🔍")
st.markdown('Tired of sifting through search results to find the \
    information you need? The Assistant can take care of it for you! \
        This open source AI-powered personal assistant can access the internet, \
            providing both quick and accurate answers to your questions.')

# Create Sidebar
with st.sidebar:
    lottie_image1 = load_lottie_url('https://assets10.lottiefiles.com/packages/lf20_ofa3xwo7.json')
    st_lottie(lottie_image1)

authenticate_user(cookie_expiry_days=0)

openai.api_key = load_api_key()

# App layout
tab1, tab2, tab3 = st.tabs(["Internet search", "Have a conversation", "Settings"])

# Internet search tab
with tab1:
    st.markdown("<span style='font-size:2em'>\
        Tell the Assistant what to research about.</span>", unsafe_allow_html=True)
    st.markdown("This tab allows you to give information from across the internet to the Assistant AI. \
        Once you've told it all the topics to search for, you can have a conversation with it in the \
            'Have a conversation' tab.")
    with st.spinner("Getting search history..."):
        google_history = get_user_search_history()
    unique_searches = google_history['query'].unique().tolist()
    unique_searches.insert(0,'')
    initial_search = st.selectbox('Search history', unique_searches, index=0)
    search = st.container()

# Have a conversation tab
with tab2:
    response = st.container()
    chat = st.container()
    settings, default_setting_index = load_assistant_settings()
    chosen_settings = st.selectbox('Assistant settings',
                                          settings.keys(),
                                          help='Determines how the assistant will behave \
                                              (Custom settings can be created in the \
                                                  conversation_settings folder).',
                                          index=default_setting_index)

    mood, warn_assistant, starting_conversation = settings[chosen_settings]

with tab3:
    logout_button()
    reset_key_button()
    delete_history_button()

# Google search section
with search:
    with st.form('Google'):
        user_query_text = st.text_input(label='Google search',value=initial_search, help="This tab \
            allows you to give information from across the internet to the Assistant AI. Once you've \
                told it all the topics to search for, you can have a conversation with it in the \
                    'Have a conversation' tab.")
        google_submitted = st.form_submit_button("Submit")
        
        query_history = google_history['query'].unique().tolist()
        
        # If the user pressed submit to make a new search or selected an existing one from history
        if (google_submitted and user_query_text != '') or initial_search != '':
            # Make an internet search if the same search was not done before
            if user_query_text not in query_history:
                search_results = google_search(user_query_text, 3)
                update_history(search_results)
            else:
                search_results = google_history    
            
            similar_results = find_top_similar_results(search_results, user_query_text, 5)
            google_findings = similar_results['text'].to_list()
            links = similar_results['link'].to_list()
            
            display_search_results(user_query_text, google_findings, links)

# Section where user inputs directly to GPT
with chat:
    with st.form('Chat'):
        user_chat_text = st.text_input(label="Ask the Assistant")
        chat_submitted = st.form_submit_button("Submit")


# User input is used here to process and display GPT's response
with response:
    load_conversation(starting_conversation)
    display_chat_history(starting_conversation)
    submit_user_message(mood, warn_assistant, user_chat_text, chat_submitted)

add_vertical_space(4)

col1, col2, col3 = st.columns(3)
with col1:
    button('farrael004', floating=False)
with col2:
    st.markdown("By [Rafael Moraes](https://github.com/farrael004)")
    badge(type="github", name="farrael004/Quest")
with col3:
    st.container()
