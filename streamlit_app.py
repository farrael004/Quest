import pandas as pd
import streamlit as st
from streamlit_lottie import st_lottie
import pickle
import threading
import openai
import requests
import bs4
import os
import json
import tiktoken
from openai.embeddings_utils import get_embedding, cosine_similarity
from datetime import datetime

tokenizer = tiktoken.get_encoding("gpt2")

def api_key_form():
    with st.form('API Key'):
        api_key = st.text_input(label='Insert your API key here')
        api_submitted = st.form_submit_button("Submit")
        api_checkbox = st.checkbox('Remember my key *(Not yet implemented in the deployed version)*', disabled=True)
            #st.markdown("NOTE: By saving your key, it will be stored in a local file without encryption.")

    st.markdown("[Find your API key here](https://beta.openai.com/account/api-keys)")
    
    # Currently inaccessible    
    if api_submitted and api_checkbox:
        f = open("api_key.txt", "a")
        f.write(api_key)
        f.close()  
    if api_submitted:
        st.session_state['api_key'] = api_key
        print(st.session_state['api_key'][-4:])
        st.experimental_rerun()
        
    st.stop()

def google_search(search: str, search_depth: int):
    try:
        res = requests.get('https://google.com/search?q=' + search)
        res.raise_for_status() # Raise if a HTTPError occured
    except:
        st.warning("There was a problem with your internet.😵  \nIf you got HTTPError: 429, that means your IP is being rate limited by Google. If you are using a VPN try disabling it. Alternatively, you can try searching again another day.😢")
        raise
    
    with st.spinner(text="Searching the internet..."):
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        
        link_elements = soup.select('a')
        links = [link.get('href').split('&sa=U&ved=')[0].replace('/url?q=', '')
                for link in link_elements
                if '/url?q=' in link.get('href') and
                'accounts.google.com' not in link.get('href') and
                'support.google.com' not in link.get('href')]
        links = list(set(links)) # Remove duplicates while maintaining the same order
        
        links_attempted = -1
        links_explored = 0
        google_results = pd.DataFrame(columns=['text', 'link', 'query'])
        link_history = st.session_state['google_history']['link'].unique().tolist()
        while links_explored < search_depth or links_attempted == len(links):
            links_attempted += 1
            if links == []:
                st.warning("No results found. 😢")
                st.stop() 
            if links[links_attempted] in link_history: continue
            # If this link does not work, go to the next one
            try:
                res = requests.get(links[links_attempted])
                res.raise_for_status()
            except:
                continue

            useful_text = extract_useful_text_from_page(res)
            link_list = [links[links_attempted] for i in range(len(useful_text))] # Creates a list of the same link to match the length of useful_text
            query_list = [search for i in range(len(useful_text))] # Creates a list of the same query to match the length of useful_text
            link_results = pd.DataFrame({'text': useful_text, 'link': link_list, 'query': query_list})
            google_results = pd.concat([google_results, link_results])
            links_explored += 1
    
    google_results['text_length'] = google_results['text'].str.len()
    largest_results = google_results.nlargest(50, 'text_length')
    largest_results = largest_results.drop_duplicates()

    with st.spinner('Analysing results...'):
        largest_results['ada_search'] = largest_results['text'].apply(lambda x: create_embedding(x))

    return largest_results

def extract_useful_text_from_page(res):
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    link_text = list(set(soup.get_text().splitlines())) # Separate all text by lines and remove duplicates
    useful_text = [s for s in link_text if len(s) > 30] # Get only strings above 30 characters
    useful_text = split_paragraphs(useful_text) # If the string is too long it will split it at full stops '. '
    useful_text = split_paragraphs(useful_text) # Do it again just for good measure (otherwise it wouldn't work for all strings for some reason. Try searching "Who is Elon Musk" to test this issue)
    return useful_text


def split_paragraphs(paragraphs, max_length=1000):
    split_paragraphs = []
    for paragraph in paragraphs:
        while len(paragraph) > max_length:
            split_index = paragraph.find('. ', max_length)
            if split_index == -1:
                # If there's no full stop after the max length, check for the next instance of '.['
                split_index = paragraph.find('.[', max_length)
                if split_index == -1:
                    # If there's no instance of '.[' after the max length, just split at the max length
                    split_index = max_length
            split_paragraph = paragraph[:split_index]
            if split_paragraph.startswith('.'):
                split_paragraph = '(...)' + split_paragraph[1:]
            else:
                split_paragraph += '(...)'
            split_paragraphs.append(split_paragraph)
            paragraph = paragraph[split_index:]
        split_paragraphs.append(paragraph)
    return split_paragraphs



def find_top_similar_results(df: pd.DataFrame, query: str, n: int):
    if len(df.index) < n:
        n = len(df.index)
    embedding = create_embedding(query)
    #embedding = get_embedding(query, engine="text-embedding-ada-002")
    df1 = df.copy()
    df1["similarities"] = df1["ada_search"].apply(lambda x: cosine_similarity(x, embedding))
    best_results = df1.sort_values("similarities", ascending=False).head(n)
    return best_results.drop(['similarities', 'ada_search'], axis=1).drop_duplicates(subset=['text'])

def create_embedding(query):
    try:
        return get_embedding(query, engine="text-embedding-ada-002")
    except:
        api_error_warning()

def api_error_warning():
    st.warning("Something went wrong.  \n  \n> An error occured when trying to send your request to OpenAI. There are a few reasons why this could happen:  \n> - This service cannot communicate with OpenAI's API.  \n> - You exceeded your rate limit. Check your usage and limit [here](https://beta.openai.com/account/usage)  \n> - You entered an invalid API key. Try getting a new key [here](https://beta.openai.com/account/api-keys) and refresh this page.", icon='⚠️')


def gpt3_call(prompt: str, tokens: int, temperature: int=1, stop=None):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=tokens,
            n=1,
            stop=stop,
            temperature=temperature)

        return response["choices"][0]["text"].replace('\n', '  \n')
    except:
        api_error_warning()
        


@st.cache
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def markdown_litteral(string: str):
    return string.replace('$','\$')

def num_of_tokens(prompt: str):
    return len(tokenizer.encode(prompt))

def update_history(results):
    history = st.session_state['google_history']

    if history.empty:
        history = results
    else:
        history = pd.concat([history, results]).drop_duplicates(subset=['text'])

    st.session_state['google_history'] = history

def load_google_history():
    # Try to find the search_history, if can't find it, create a new search_history
    try:
        with open('search_history.pickle', 'rb') as f:
            return pickle.load(f)
    except:
        data = pd.DataFrame(columns=['text', 'link', 'query', 'text_length', 'ada_search'])
        #with open('search_history.pickle', 'wb') as f:
            #pickle.dump(data, f)
        return data

def save_google_history(data):
    #with open('search_history.pickle', 'wb') as f:
        #pickle.dump(data, f)
    pass
        
def save_google_history_in_thread(data):
    thread = threading.Thread(target=save_google_history, args=(data))
    thread.start()
    
def add_conversation_entry(new_entry):
    text_length = len(new_entry)
    data = pd.DataFrame({'text': new_entry, 'text_length': text_length}, index=[0])
    data['ada_search'] = data['text'].apply(lambda x: create_embedding(x))
    st.session_state['conversation'] = pd.concat([st.session_state['conversation'], data], ignore_index=True)

st.set_page_config(page_title='Quest🔍')
st.title("Quest🔍")
st.markdown("By [Rafael Moraes](https://github.com/farrael004)")

# Load Assistant settings
script_path = os.path.abspath(__file__).replace('streamlit_app.py', '')
folder_path = os.path.join(script_path, 'conversation_settings')
file_names = os.listdir(folder_path)
all_settings = []
for file_name in file_names:
    if file_name.endswith('.json'):
        with open(os.path.join(folder_path, file_name)) as f:
            data = json.load(f)
            all_settings.append(data)

settings = {setting['setting_name']: (setting['mood'], setting['warn_assistant'], pd.DataFrame(setting['starting_conversation'])) for setting in all_settings}
default_setting = 'Strictly Factual'
default_setting_index = list(settings.keys()).index(default_setting)

with st.sidebar:
    lottie_image1 = load_lottie_url('https://assets10.lottiefiles.com/packages/lf20_ofa3xwo7.json')
    st_lottie(lottie_image1)

# Load the API key
if 'api_key' not in st.session_state:
    try:
        with open('api_key.txt') as api_key:
            st.session_state['api_key'] = api_key.read()
    except:
        api_key_form()

openai.api_key = st.session_state['api_key']

# Defining google search history
if 'google_history' not in st.session_state:
    st.session_state['google_history'] = load_google_history()

if 'google_findings' not in st.session_state:
    st.session_state['google_findings'] = []
if 'links' not in st.session_state:
    st.session_state['links'] = []
if 'user_query' not in st.session_state:
    st.session_state['user_query'] = []

google_findings = st.session_state['google_findings']
links = st.session_state['links']
user_query = st.session_state['user_query']

# App layout
tab1, tab2 = st.tabs(["Internet search", "Have a conversation"])

with tab1:
    st.markdown("## Tell the Assistant what to research about.")
    st.markdown("This tab allows you to give information from across the internet to the Assistant AI. \
        Once you've told it all the topics to search for, you can have a conversation with it in the 'Have a \
            conversation' tab.")
    search_history = st.session_state['google_history']['query'].unique().tolist()
    search_history.insert(0,'')
    initial_search = st.selectbox('Search history', search_history, index=0)
    search = st.container()
    
with tab2:
    response = st.container()
    chat = st.container()
    chosen_settings = st.selectbox('Assistant settings',
                                          settings.keys(),
                                          help='Determines how the assistant will behave \
                                              (Custom settings can be created in the \
                                                  conversation_settings folder).',
                                          index=default_setting_index)

    mood, warn_assistant, starting_conversation = settings[chosen_settings]

# Google search section
with search:
    with st.form('Google'):
        user_query_text = st.text_input(label='Google search',value=initial_search, help="This tab \
            allows you to give information from across the internet to the Assistant AI. Once you've \
                told it all the topics to search for, you can have a conversation with it in the \
                    'Have a conversation' tab.")
        google_submitted = st.form_submit_button("Submit")
        
        query_history = st.session_state['google_history']['query'].unique().tolist()
        # If the user pressed submit to make a new search or selected an existing one from history
        if (google_submitted and user_query_text != '') or initial_search != '':
            if user_query_text not in query_history:
                search_results = google_search(user_query_text, 3)
                update_history(search_results)
                save_google_history(st.session_state['google_history'])
            else:
                search_results = st.session_state['google_history']    
            
            similar_results = find_top_similar_results(search_results, user_query_text, 5)
            
            st.session_state['google_findings'] = similar_results['text'].to_list()
            google_findings = st.session_state['google_findings']
            
            st.session_state['links'] = similar_results['link'].to_list()
            links = st.session_state['links']
            
            st.session_state['user_query'] = user_query_text
            user_query = st.session_state['user_query']
            
            if len(user_query) > 0:
                st.markdown('---')
                st.markdown(f'# {user_query}')
                for i,finding in enumerate(google_findings):
                    st.markdown(markdown_litteral(finding) + f' [Source]({links[i]})')

# Section where user inputs directly to GPT
with chat:
    with st.form('Chat'):
        user_chat_text = st.text_input(label="Ask the Assistant")
        chat_submitted = st.form_submit_button("Submit")

# Initialize the conversation if it was not initialized before or if the assistant settings changed
if 'conversation' not in st.session_state or starting_conversation['text'].to_list() != st.session_state['conversation']['text'].iloc[:len(starting_conversation.index)].to_list():
    st.session_state['conversation'] = starting_conversation

with response:
    # Show conversation so far
    chat_so_far = ''
    for i, text in enumerate(st.session_state['conversation']['text']):
        chat_so_far += text + '\n'
        if i < len(starting_conversation): continue
        if text[:4] == 'User':
            text = '👤' + text[:-10]
        else:
            text = '🖥️' + markdown_litteral(text[:-10])
        st.write(text)
        st.markdown('---')

    # Submits new prompt
    if chat_submitted and user_chat_text != '':
        st.write('👤User: ' + user_chat_text)

        with st.spinner('Sending message...'):
            similar_google_results = find_top_similar_results(st.session_state['google_history'], user_chat_text, 5)
            similar_conversation = find_top_similar_results(st.session_state['conversation'], user_chat_text, 4)
        
        # Knowing the current time and date may be important for interpreting news articles.
        date = datetime.now()
        current_date_and_time = f'Current time is {date.strftime("%I")}:{date.strftime("%M")} {date.strftime("%p")} {date.strftime("%A")} {date.strftime("%B")} {date.day} {date.year}.\n'
        
        prompt = mood + current_date_and_time
        if similar_google_results.empty:
            prompt += "The user did not make a google search to provide more information.\n"
        else:
            prompt += "The user provided you with google searches.\nYour findings are: " + \
                    '\n'.join(similar_google_results['text'].to_list()) + "\n"
            
        prompt += 'These are the relevant entries from the conversation so far (in order of importance):\n' + \
            '\n'.join(similar_conversation['text'].to_list()) + '\nThese are the last two messages:\nAssistant: ' + st.session_state['conversation']['text'].iloc[-1] + '\nUser: ' + user_chat_text + warn_assistant + '\nAssistant:'

        tokens = num_of_tokens(prompt)
        with st.spinner('Generating response...'):
            answer = gpt3_call(prompt, tokens=4000 - tokens, stop='User:')
        add_conversation_entry('User: ' + user_chat_text + f'({date.strftime("%I")}:{date.strftime("%M")} {date.strftime("%p")})')
        add_conversation_entry('Assistant: ' + answer + f'({date.strftime("%I")}:{date.strftime("%M")} {date.strftime("%p")})')
        st.markdown('---')
        st.write('🖥️Assistant: ' + markdown_litteral(answer))
        with st.expander("What sources did I use to make this answer?"):
            for row in similar_google_results.iterrows():
                st.write(markdown_litteral(row[1]['text']) + f" [Source]({row[1]['link']})") 
        with st.expander("Prompt used:"):
            st.write(markdown_litteral(prompt).replace('\n','  \n  \n'))
            st.markdown(':green[Tokens used: ]' + f':green[{str(num_of_tokens(prompt))}]')
