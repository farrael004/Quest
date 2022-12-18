# To create a new setting, simply change setting_name, warn_assistant, and
# starting_conversation. Then run this script.

setting_name = 'Template'
warn_assistant = "\nWARNING: If the user asks for information that is not in their google search, try to answer the question as factualy as possible and warn the user about this absence. DO NOT provide any hyperlinks.\n"
starting_conversation = ['User: Who are you?',
                         'Assistant: Hello, my name is Assistant. How can I help you?',
                         'User: How much is the toy car from my search?',
                         "Assistant: Unfortunately your Google search did not specify prices for gifts, but based on your search, I do have some information about popular gifts for kids in 2022.",
                         "User: Can you show me how to loop between 0 and 9 in python?",
                         "Assistant: Sure. Here's how you can loop between 0 and 9 in python:\n```python\nfor i in range(10):\n    print(i)\n```"]

import pandas as pd
from openai.embeddings_utils import get_embedding, cosine_similarity
import openai
import json
import os

# Navigate to the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
with open(os.path.join(parent_dir, 'api_key.txt'), 'r') as f:
    openai.api_key = f.read()

text_length = [len(x) for x in starting_conversation]
data = pd.DataFrame({'text': starting_conversation, 'text_length': text_length})
print('Creating embeddings...')
data['ada_search'] = data['text'].apply(lambda x: get_embedding(x, engine='text-embedding-ada-002'))

dictionary = {
    "setting_name": setting_name,
    "warn_assistant": warn_assistant,
    "starting_conversation": data.to_dict()
}

# Serializing json
json_object = json.dumps(dictionary, indent=4)
 
# Writing to file
file_name = setting_name.replace(' ', '_') + ".json"
with open(file_name, "w") as outfile:
    outfile.write(json_object)
    
print('Setting successfully created. You may close this window')