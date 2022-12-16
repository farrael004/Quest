import streamlit as st
from urllib.error import HTTPError
import openai
import requests
import bs4

from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

@st.cache(suppress_st_warning=True)
def google_search(search: str):
    res = requests.get('https://google.com/search?q=' + search)
    
    # Raise if a HTTPError occured
    try:
        res.raise_for_status()
    except HTTPError as err:
        if err.code == 429:
            st.warning("😵 Your IP is being rate limited by Google. If you are using a VPN try disabling it. Alternatively, you can try searching again another day.😢")
            raise err
        else:
            raise err

    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    link_elements = soup.select('a')
    links = {link.get('href').split('&sa=U&ved=')[0].replace('/url?q=', '')
             for link in link_elements
             if '/url?q=' in link.get('href') and
             'accounts.google.com' not in link.get('href') and
             'support.google.com' not in link.get('href')}
    text = soup.get_text(separator='\n')
    
    
    # Here I'm predicting where the useful information in the string is. Since some have reported different formatting, it is in a try block.
    try:
        text = text.split('All results\nAll results\nVerbatim\n')[1]
    except:
        pass
    try:
        text = text.split('Next >')[0]
    except:
        pass

    return text, list(links)


@st.cache
def gpt3_call(prompt: str, tokens: int, temperature: int = 1, stop=None):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=tokens,
        n=1,
        stop=stop,
        temperature=temperature)

    return response["choices"][0]["text"].replace('\n', '  \n')

def markdown_litteral(string: str):
    return string.replace('$','\$')

def num_of_tokens(prompt: str):
    return len(tokenizer(prompt)['input_ids'])


st.set_page_config(page_title='Quest🔍')
st.title("Quest🔍")
st.markdown("By [Rafael Moraes](https://github.com/farrael004)")
st.markdown('---')

# Setting how factual/creative the model will be. This can be tunned.
assistant_settings = st.sidebar.selectbox('Assistant settings',
                                          ['Strictly Factual', 'Factual', 'Neutral', 'Creative', 'Very Creative'],
                                          help='Determines how close to the facts already presented the Assistent will be.',
                                          index=2)

match assistant_settings:
    case 'Strictly Factual':
        warn_assistant = "\nWARNING: If the user asks for information that is not in their google search, try to answer the question as factualy as possible and warn the user about this absence. DO NOT provide any hyperlinks.\n"
        starting_conversation = ['User: Who are you?',
                                 'Assistant: Hello, my name is Assistant. How can I help you?',
                                 'User: How much is the toy car from my search?',
                                 "Assistant: Unfortunately your Google search did not specify prices for gifts, but based on your search, I do have some information about popular gifts for kids in 2022.",
                                 "User: Can you show me how to loop between 0 and 9 in python?",
                                 "Assistant: Sure. Here's how you can loop between 0 and 9 in python:\n```python\nfor i in range(10):\n    print(i)\n```"]

    case 'Factual':
        warn_assistant = "\nWARNING: If the user asks for information that is not in their google search, try to answer the question but warn about potential lack of precise or up to date information. DO NOT provide any hyperlinks.\n"
        starting_conversation = ['User: Who are you?',
                                 'Assistant: Hello, my name is Assistant. How can I help you?',
                                 'User: How much is the toy car from my search?',
                                 "Assistant: Unfortunately your Google search did not specify prices for gifts, but I do have some information about popular gifts for kids in 2022.",
                                 "User: Can you show me how to loop between 0 and 9 in python?",
                                 "Assistant: Sure. Here's how you can loop between 0 and 9 in python:\n```python\nfor i in range(10):\n    print(i)\n```"]
    case 'Neutral':
        warn_assistant = "\nATTENTION: If the user asks for information that is not in their google search, try to answer the question to the best of your knowledge but warn about potential lack of precise or up to date information.\n"
        starting_conversation = ['User: Who are you?',
                                 'Assistant: Hello, my name is Assistant. How can I help you?',
                                 'User: How much is the toy car from my search?',
                                 "Assistant: Unfortunately your Google search did not specify prices for gifts, but I do have some information about popular gifts for kids in 2022.",
                                 "User: Can you show me how to loop between 0 and 9 in python?",
                                 "Assistant: Sure. Here's how you can loop between 0 and 9 in python:\n```python\nfor i in range(10):\n    print(i)\n```"]
    case 'Creative':
        warn_assistant = "\nATTENTION: If the user asks for information that is not in their google search, try to answer the question in a way that seems correct but warn about potential lack of precise or up to date information.\n"
        starting_conversation = ['User: Who are you?',
                                 'Assistant: Hello, my name is Assistant. How can I help you?',
                                 'User: How much is the toy car from my search?',
                                 "Assistant: Unfortunately your Google search did not specify prices for gifts, but I do have some information about popular gifts for kids in 2022.",
                                 "User: Can you show me how to loop between 0 and 9 in python?",
                                 "Assistant: Sure. Here's how you can loop between 0 and 9 in python:\n```python\nfor i in range(10):\n    print(i)\n```"]
    case 'Very Creative':
        warn_assistant = ''
        starting_conversation = ['User: Who are you?',
                                 'Assistant: Hello, my name is Assistant. How can I help you?',
                                 "User: Can you show me how to loop between 0 and 9 in python?",
                                 "Assistant: Sure. Here's how you can loop between 0 and 9 in python:\n```python\nfor i in range(10):\n    print(i)\n```"]

# Load the API key from a local file
try:
    with open('api_key.txt') as api_key:
        openai.api_key = api_key.read()
except:
    st.markdown(
        "Put a file called 'api_key.txt' in the Quest folder. Make sure the file has your OpenAI API key inside.")
    st.markdown("[Find your API key here](https://beta.openai.com/account/api-keys)")
    st.stop()

# App layout
response = st.container()
chat = st.container()
search = st.expander('Google Search', expanded=True)

# Defining google search history
if 'google_findings' not in st.session_state:
    st.session_state['google_findings'] = ['']
if 'google_links' not in st.session_state:
    st.session_state['google_links'] = [[]]
if 'user_queries' not in st.session_state:
    st.session_state['user_queries'] = ['']

google_findings = st.session_state['google_findings']
links = st.session_state['google_links']
user_queries = st.session_state['user_queries']

# Google search section
with search:
    with st.form('Google'):
        user_query_text = st.text_input(label='')
        google_submitted = st.form_submit_button("Submit")

        if google_submitted:
            st.session_state['user_queries'].append(user_query_text)
            search_results, search_links = google_search(user_query_text)
            st.session_state['google_links'].append(search_links)
            prompt = "The user google searched the following:\n" + user_query_text + "\nThe results are:\n" + search_results + "\nWrite all of the relevant information to the user's search based on the results:"
            tokens = num_of_tokens(prompt)
            st.session_state['google_findings'].append(gpt3_call(prompt, 4000 - tokens, temperature=0))

    # Iterate backwards so older searches are at the bottom
    for i in range(len(google_findings) - 1, -1, -1):
        if i == 0: continue
        st.markdown('---')
        st.markdown(f'# {user_queries[i]}')
        st.markdown(markdown_litteral(google_findings[i]))
        if len(links[i]) > 0:
            st.markdown('---')
            st.write('Sources:')
            for link in links[i]:
                st.write(link)

# Section where user inputs directly to GPT
with chat:
    with st.form('Chat'):
        user_chat_text = st.text_input(label="Ask me anything")
        chat_submitted = st.form_submit_button("Submit")

# Initialize the conversation if it was not initialized before or if the assistant settings changed
if 'conversation' not in st.session_state or starting_conversation != st.session_state['conversation'][:len(starting_conversation)]:
    st.session_state['conversation'] = starting_conversation

with response:
    # Show conversation so far
    chat_so_far = ''
    for i, text in enumerate(st.session_state['conversation']):
        chat_so_far += text + '\n'
        if i < len(starting_conversation): continue
        if text[:4] == 'User':
            text = '👤' + text
        else:
            text = '🖥️' + markdown_litteral(text)
        st.write(text)
        st.markdown('---')

    # Submits new prompt
    if chat_submitted:
        st.write('👤User: ' + user_chat_text)
        st.session_state['conversation'].append('User: ' + user_chat_text)

        prompt = 'You are a friendly and helpful AI assistant. You have access to the internet if the user makes a google search.\n'
        if google_findings[-1] != '':
            prompt += "The user asked you to google search:\n" + user_queries[-1] + "\nYour findings are:" + \
                      google_findings[-1] + "\n"
        else:
            prompt += "The user did not make a google search to provide more information.\n"
        prompt += 'This is the conversation so far:\n' + chat_so_far + 'User: ' + user_chat_text + warn_assistant + '\nAssistant:'

        tokens = num_of_tokens(prompt)
        answer = gpt3_call(prompt, tokens=4000 - tokens, stop='User:')
        st.session_state['conversation'].append('Assistant: ' + answer)
        print(prompt + answer)
        st.markdown('---')
        st.write('🖥️Assistant: ' + answer)
