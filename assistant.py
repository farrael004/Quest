import re
import os
import json
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import pandas as pd
from datetime import datetime
from gpt_api import find_top_similar_results, gpt3_call
from gpt_api import create_embedding
from utils import markdown_litteral, num_of_tokens
from internet_search import *


def load_assistant_settings():
    own_script_name = os.path.basename(__file__)
    script_path = os.path.abspath(__file__).replace(own_script_name, '')
    folder_path = os.path.join(script_path, 'conversation_settings')
    file_names = os.listdir(folder_path)
    all_settings = []
    for file_name in file_names:
        if file_name.endswith('.json'):
            with open(os.path.join(folder_path, file_name)) as f:
                data = json.load(f)
                all_settings.append(data)

    archetypes = {setting['setting_name']: {'mood':setting['mood'],
                                            'warn_assistant':setting['warn_assistant'],
                                            'starting_conversation':pd.DataFrame(setting['starting_conversation'])}
                    for setting in all_settings}
    
    default_setting = 'Strictly Factual'
    default_setting_index = list(archetypes.keys()).index(default_setting)
                
    return archetypes, default_setting_index


def load_conversation(starting_conversation):
    # load conversation if it is not loaded or if the initial conversation has changed.
    #if ('conversation' not in st.session_state 
    #or starting_conversation['text'].to_list() != 
    #st.session_state['conversation']['text'].iloc[:len(starting_conversation.index)].to_list()):
    if 'conversation' not in st.session_state:
        st.session_state['conversation'] = starting_conversation


def display_chat_history(starting_conversation):
    chat_so_far = ''
    for i, text in enumerate(st.session_state['conversation']['text']):
        chat_so_far += text + '\n'
        if i < len(starting_conversation): continue
        if text[:4] == 'User':
            text = '👤' + text[:-13]
        else:
            text = '🖥️' + markdown_litteral(text[:-13])
        st.write(text)
        st.markdown('---')
     
        
def add_conversation_entry(new_entry):
    text_length = len(new_entry)
    data = pd.DataFrame({'text': new_entry, 'text_length': text_length}, index=[0])
    data['ada_search'] = data['text'].apply(lambda x: create_embedding(x))
    st.session_state['conversation'] = pd.concat([st.session_state['conversation'], data],
                                                 ignore_index=True)
        

def create_prompt(settings,
                  user_chat_text,
                  similar_google_results,
                  similar_conversation,
                  current_time,
                  current_date_and_time):
    
    mood = settings['archetype']['mood']
    warn_assistant = settings['archetype']['warn_assistant']

    prompt = mood + current_date_and_time
    if similar_google_results.empty:
        prompt += "The user did not make a google search to provide more information.\n"
    else:
        prompt += "The user provided you with google searches and your findings from different \
                sources are:  \n" + '\n'.join(similar_google_results['text'].to_list()) + "\n"
    prompt += 'These are the relevant entries from the conversation so far (in order of importance):\n' + \
            '\n'.join(similar_conversation['text'].to_list()) + '\nThese are the last two messages:\n\
                ' + st.session_state['conversation']['text'].iloc[-1] + warn_assistant #'\nUser: \
                    #' + user_chat_text + f' ({current_time})\n' + warn_assistant  + '\nAssistant:'
                    
    prompt_model = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': user_chat_text}
    ]
           
    return prompt, prompt_model

def display_assistant_response(similar_google_results, prompt, answer):
    st.markdown('---')
    st.write('🖥️Assistant: ' + markdown_litteral(answer))
    with st.expander("What sources did I use to make this answer?"):
        for row in similar_google_results.iterrows():
            st.write(markdown_litteral(row[1]['text']) + f" [Source]({row[1]['link']})") 
    with st.expander("Prompt used:"):
        st.write(markdown_litteral(prompt).replace('\n','  \n  \n'))
        st.markdown(':green[Tokens used: ]' + f':green[{str(num_of_tokens(prompt))}]')
   

def assistant_settings(chat_submitted, col2):
    settings = {}
    if 'answer_with_search' not in st.session_state['settings']:
        st.session_state['settings']['answer_with_search'] = True
    settings['answer_with_search'] = col2.checkbox('Search internet to answer',
                                        value=True,
                                        help="When checked, the Assistant will make a new \
                                            search using your question as the query. If you \
                                                disable this, the Assistant will use only the \
                                                        search history.")
    with st.expander("Assistant settings"):
        col1, col2 = st.columns(2)
        archetypes, default_setting_index = load_assistant_settings()
        archetype = col1.selectbox('Archetype',
                                                archetypes.keys(),
                                                help='Determines how the assistant will behave \
                                                    (Custom archetypes can be created in the \
                                                        "Create your Assistant" tab).',
                                                index=default_setting_index)
            
        if 'num_of_excerpts' not in st.session_state['settings']:
            st.session_state['settings']['num_of_excerpts'] = 5
            st.session_state['settings']['consult_search_history'] = True
            st.session_state['settings']['specify_sources'] = ''
            st.session_state['settings']['temperature'] = 1.0
                  
        settings['temperature'] = col2.slider('Temperature',
                                              min_value=0.0,max_value=1.0,value=1.0,step=0.01,
                                              help="Determine how random the Assistant responses are \
                                                  lower numbers mean more deterministic answers \
                                                      higher values mean more random.") 
        
        settings['specify_sources'] = st.text_input("Specify links",
                                                        help="This field allows you to specify urls \
                                                            for the Assistant to source from. \
                                                                Separate each link with a comma \
                                                                    and space `, `.",
                                                                    value='') 
        with col2.container():
            add_vertical_space(1)
            
        settings['consult_search_history'] = col2.checkbox('Consult search history',
                                                             value=True,
                                                             help="When checked, the Assistant will look into \
                                                                 the search history to find relevant excerpts.")  
        
        settings['num_of_excerpts'] = col1.number_input('How many excerpts to use',
                                                          min_value=1,
                                                          value=5,
                                                          help='This indicates how many \
                                                              pieces of texts from searches \
                                                                  to use in the prompt') 
        
    if chat_submitted:
        settings['archetype'] = archetypes[archetype]
        st.session_state['settings'] = settings
        
                                                                
    return settings        
        
        
def submit_user_message(settings, user_chat_text, chat_submitted):
    if not chat_submitted or user_chat_text == '': return
    
    # Show user message
    st.write('👤User: ' + user_chat_text)

    # Find relevant search results and conversation entries to craft the AI prompt
    similar_google_results = get_info_from_internet(user_chat_text, settings)
    with st.spinner('Sending message...'):
        similar_conversation = find_top_similar_results(st.session_state['conversation'],
                                                        user_chat_text, 4)
    
    # Knowing the current time and date may be important for interpreting news articles.
    date = datetime.now()
    current_time = f'{date.strftime("%I:%M:%S %p")}'
    current_date_and_time = f'Current time is {date.strftime("%I:%M %p %A %B %d %Y")}.\n'
    
    prompt_text, prompt_model = create_prompt(
        settings,
        user_chat_text,
        similar_google_results,
        similar_conversation,
        current_time,
        current_date_and_time
    )
    
    tokens = num_of_tokens(prompt_text)
    
    # Send prompt to the AI and record it to chat history
    with st.spinner('Generating response...'):
        answer = gpt3_call(prompt_model,
                           tokens=4000 - tokens,
                           temperature=settings['temperature'],
                           stop='User:')
        answer = remove_timestamp(answer)
    add_conversation_entry('User: ' + user_chat_text + f' ({current_time})')
    current_time = f'{date.strftime("%I:%M:%S %p")}'
    add_conversation_entry('Assistant: ' + answer + f' ({current_time})')
    
    display_assistant_response(similar_google_results, prompt_text, answer)


def add_searches(settings):
    with st.expander("Add searches"):
        num_of_queries = st.number_input("Number of additional searches", min_value=0, value=1)
        
        settings['additional_searches'] = []
        for i in range(num_of_queries):
            search = st.text_input("Search query", key=i)
            if search != '':
                settings['additional_searches'].append(search)
                
    return settings


def get_info_from_internet(user_chat_text, settings):
    answer_with_search = settings['answer_with_search']
    additional_searches = settings['additional_searches']
    specify_sources = settings['specify_sources'].split(', ')
    consult_search_history = settings['consult_search_history']
    num_of_excerpts = settings['num_of_excerpts']

    history = st.session_state['google_history']
    
    sources_content = pd.DataFrame()
    if specify_sources != ['']:
        sources_content = search_new_links(user_chat_text, specify_sources, history, sources_content)
    
    if additional_searches != []:
        sources_content = search_new_queries(additional_searches, history, sources_content)
            
    if answer_with_search:       
       sources_content = search_new_queries([user_chat_text], history, sources_content)
        
    if not consult_search_history:
        if sources_content.empty: return pd.DataFrame()
        return find_top_similar_results(sources_content, user_chat_text, num_of_excerpts)
    
    all_results = st.session_state['google_history']
    all_results = pd.concat([all_results, sources_content])
        
    return find_top_similar_results(all_results, user_chat_text, num_of_excerpts)

def search_new_links(user_chat_text, specify_sources, history, sources_content):
    already_seen_results = history[history['link'].isin(specify_sources)]
    links_not_in_history = [value for value in specify_sources if value not in history['link'].values]
    #print()
    if all_are_valid_links(links_not_in_history):
        sources_content = page_search(user_chat_text,len(links_not_in_history),links_not_in_history)
        update_history(sources_content)
        sources_content = pd.concat([sources_content, already_seen_results])
    return sources_content

def search_new_queries(additional_searches, history, sources_content):
    already_seen_results = history[history['query'].isin(additional_searches)]
    query_not_in_history = [value for value in additional_searches if value not in history['query'].values]
    sources_content = pd.concat([sources_content, already_seen_results])
    queries_results = pd.DataFrame()
    for search in query_not_in_history:
        query_results = ddg_search(search, 3)
        queries_results = pd.concat([queries_results,query_results])
    update_history(queries_results)
    sources_content = pd.concat([sources_content, queries_results])
    return sources_content

def remove_timestamp(string):
    # Compile a regex pattern to match the timestamp at the end of the string
    pattern = re.compile(r'\(\d\d:\d\d:\d\d [AP]M\)$')
    return pattern.sub('', string) # Use the regex to replace the timestamp with an empty string