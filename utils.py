from tiktoken import get_encoding
import streamlit as st
import requests
from logging import warning
from itertools import zip_longest

tokenizer = get_encoding("gpt2")
def num_of_tokens(prompt: str):
    return len(tokenizer.encode(prompt))

def markdown_litteral(string: str):
    return string.replace('$','\$')

@st.cache
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        warning(f'Could not find lottie from url {url}.')
        return None
    
def api_error_warning():
    st.warning("Something went wrong.  \n  \n> An error occured when trying to send your request to OpenAI.There are a few reasons why this could happen:  \n> - This service cannot communicate with OpenAI's API.  \n> - You exceeded your rate limit. Check your usage and limit [here](https://beta.openai.com/account/usage)  \n> - You entered an invalid API key. Try getting a new key [here](https://beta.openai.com/account/api-keys) and reset your API key in the settings tab.",
            icon='⚠️')
    
def separate_list(iterable, n):
    # Collect data into fixed-length chunks or blocks
    args = [iter(iterable)] * n
    groups = zip_longest(*args, fillvalue=None) # ('ABCDEFG', 3, 'None') --> ((A,B,C), (D,E,F), (G,None,None))
    result = list(groups)
    return [list(filter(lambda x: x is not None, sublist)) for sublist in result] # Remove None

def tell_to_reload_page():
    st.write("# 🔄Reload the page")   
    st.write("Reload this page to apply changes")
    st.stop()