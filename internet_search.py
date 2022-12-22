import streamlit as st
import bs4
import requests
import pickle
import threading
import pandas as pd
import database as db
from gpt_api import create_embedding
from utils import markdown_litteral


def google_search(search: str, search_depth: int):
    # Make a search request
    try:
        res = requests.get('https://google.com/search?q=' + search)
        res.raise_for_status() # Raise if a HTTPError occured
    except:
        st.warning("There was a problem with this services's internet.😵  \n\
                    If you got HTTPError: 429, that means this services's IP \
                    is being rate limited by Google. If you experience this, \
                    please report the issue at https://github.com/farrael004/Quest/issues.")
        raise
    
    with st.spinner(text="Searching the internet..."):
        # Extract link results from the search request
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        link_elements = soup.select('a')
        links = [link.get('href').split('&sa=U&ved=')[0].replace('/url?q=', '')
                for link in link_elements
                if '/url?q=' in link.get('href') and
                'accounts.google.com' not in link.get('href') and
                'support.google.com' not in link.get('href')]
        links = list(set(links)) # Remove duplicates while maintaining the same order
        
        # Explore the links
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
            
            # Create a table with the useful texts from the page, the page's link, and the query used 
            useful_text = extract_useful_text_from_page(res)
            link_list = [links[links_attempted] for i in range(len(useful_text))] # Creates a list of the same link to match the length of useful_text
            query_list = [search for i in range(len(useful_text))] # Creates a list of the same query to match the length of useful_text
            link_results = pd.DataFrame({'text': useful_text, 'link': link_list, 'query': query_list})
            google_results = pd.concat([google_results, link_results])
            links_explored += 1
    
    # Filter for only the largest results
    google_results['text_length'] = google_results['text'].str.len()
    largest_results = google_results.nlargest(50, 'text_length')
    largest_results = largest_results.drop_duplicates()

    # Create embeddings
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
        # Split the paragraph until no parts are larger than the max length
        while len(paragraph) > max_length:
            split_index = paragraph.find('. ', max_length)
            # If there's no '. ' after the max length, check for the next instance of '.['
            if split_index == -1:
                split_index = paragraph.find('.[', max_length)
                # If there's no instance of '.[' after the max length, just split at the max length
                if split_index == -1:
                    split_index = max_length
            split_paragraph = paragraph[:split_index]
            # Indicate where strings were split with '(...)'
            if split_paragraph.startswith('.'):
                split_paragraph = '(...)' + split_paragraph[1:]
            else:
                split_paragraph += '(...)'
            split_paragraphs.append(split_paragraph)
            paragraph = paragraph[split_index:]
        split_paragraphs.append(paragraph)
    return split_paragraphs


def load_google_history():
    # Try to find the search history, if can't find it, create a new search history
    try:
        return db.get_user_search_history(st.session_state['username'])
    except:
        data = pd.DataFrame(columns=['text', 'link', 'query', 'text_length', 'ada_search'])
        return data


def save_google_history(results):
    for data in results:
        db.insert_search_history(st.session_state['username'], data)
  
        
def save_google_history_in_thread(results):
    thread = threading.Thread(target=save_google_history, args=(results))
    thread.start()
    
    
def get_user_search_history():
    if 'google_history' not in st.session_state:
        st.session_state['google_history'] = load_google_history()
    return st.session_state['google_history']
  
   
def update_history(results):
    save_google_history(results.to_dict('records'))
    history = st.session_state['google_history']

    if history.empty:
        history = results
    else:
        history = pd.concat([history, results]).drop_duplicates(subset=['text'])

    st.session_state['google_history'] = history
   
    
def display_search_results(user_query_text, google_findings, links):
    if len(user_query_text) > 0:
        st.markdown('---')
        st.markdown(f'# {user_query_text}')
        for i,finding in enumerate(google_findings):
            st.markdown(markdown_litteral(finding) + f' [Source]({links[i]})')
 
            
def delete_search_history():
    db.delete_search_history(st.session_state['username'])


def delete_history_button():
    st.button('Delete search history', on_click=delete_search_history)