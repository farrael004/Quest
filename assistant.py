import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from gpt_api import find_top_similar_results, gpt3_call
from gpt_api import create_embedding
from utils import markdown_litteral, num_of_tokens

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

    settings = {setting['setting_name']: (setting['mood'],
                                      setting['warn_assistant'],
                                      pd.DataFrame(setting['starting_conversation']))
            for setting in all_settings}
    
    default_setting = 'Strictly Factual'
    default_setting_index = list(settings.keys()).index(default_setting)
                
    return settings, default_setting_index


def load_conversation(starting_conversation):
    if ('conversation' not in st.session_state 
    or starting_conversation['text'].to_list() != 
    st.session_state['conversation']['text'].iloc[:len(starting_conversation.index)].to_list()):
        st.session_state['conversation'] = starting_conversation


def display_chat_history(starting_conversation):
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
        
def add_conversation_entry(new_entry):
    text_length = len(new_entry)
    data = pd.DataFrame({'text': new_entry, 'text_length': text_length}, index=[0])
    data['ada_search'] = data['text'].apply(lambda x: create_embedding(x))
    st.session_state['conversation'] = pd.concat([st.session_state['conversation'], data],
                                                 ignore_index=True)
        

def create_prompt(mood,
                  warn_assistant,
                  user_chat_text,
                  similar_google_results,
                  similar_conversation,
                  current_time,
                  current_date_and_time):
    
    prompt = mood + current_date_and_time
    if similar_google_results.empty:
        prompt += "The user did not make a google search to provide more information.\n"
    else:
        prompt += "The user provided you with google searches and your findings from different \
                sources are:  \n" + '\n'.join(similar_google_results['text'].to_list()) + "\n"
    prompt += 'These are the relevant entries from the conversation so far (in order of importance):\n' + \
            '\n'.join(similar_conversation['text'].to_list()) + '\nThese are the last two messages:\n\
                ' + st.session_state['conversation']['text'].iloc[-1] + '\nUser: \
                    ' + user_chat_text + f' ({current_time})' + warn_assistant + '\nAssistant:'
                
    return prompt


def display_assistant_response(similar_google_results, prompt, answer):
    st.markdown('---')
    st.write('🖥️Assistant: ' + markdown_litteral(answer))
    with st.expander("What sources did I use to make this answer?"):
        for row in similar_google_results.iterrows():
            st.write(markdown_litteral(row[1]['text']) + f" [Source]({row[1]['link']})") 
    with st.expander("Prompt used:"):
        st.write(markdown_litteral(prompt).replace('\n','  \n  \n'))
        st.markdown(':green[Tokens used: ]' + f':green[{str(num_of_tokens(prompt))}]')
        
def submit_user_message(mood, warn_assistant, user_chat_text, chat_submitted):
    if not chat_submitted or user_chat_text == '': return
    
    # Show user message
    st.write('👤User: ' + user_chat_text)

    # Find relevant search results and conversation entries to craft the AI prompt
    with st.spinner('Sending message...'):
        similar_google_results = find_top_similar_results(st.session_state['google_history'],
                                                            user_chat_text, 5)
        similar_conversation = find_top_similar_results(st.session_state['conversation'],
                                                        user_chat_text, 4)
    
    # Knowing the current time and date may be important for interpreting news articles.
    date = datetime.now()
    current_time = f'{date.strftime("%I")}:{date.strftime("%M")} {date.strftime("%p")}'
    current_date_and_time = f'Current time is {current_time} \
            {date.strftime("%A")} {date.strftime("%B")} {date.day} {date.year}.\n'
    
    prompt = create_prompt(mood,
                            warn_assistant,
                            user_chat_text,
                            similar_google_results,
                            similar_conversation,
                            current_time,
                            current_date_and_time)
    
    tokens = num_of_tokens(prompt)
    
    # Send prompt to the AI and record it to chat history
    with st.spinner('Generating response...'):
        answer = gpt3_call(prompt, tokens=4000 - tokens, stop='User:')
    add_conversation_entry('User: ' + user_chat_text + f' ({current_time})')
    add_conversation_entry('Assistant: ' + answer + f' ({current_time})')
    
    display_assistant_response(num_of_tokens, similar_google_results, prompt, answer)