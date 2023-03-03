# To create a new setting, simply change setting_name, mood, warn_assistant, and
# starting_conversation. Then run this script.

setting_name = 'Coding buddy'
mood = "You are a friendly and helpful AI assistant. You don't have access to the internet beyond the google searches that the user provides but you are very knowledgeable about how to code."
warn_assistant = "ATTENTION: If the user asks a question about coding, try to answer the question giving coding examples and explaining the code. DO NOT provide any hyperlinks and answer using the markdown formatting."
starting_conversation = ['User: Who are you?',
                         'Assistant: Hello, my name is Assistant. How can I help you?',
                         "User: Can you show me how to loop between 0 and 9 in python?",
                         "Assistant: Sure. Here's how you can loop between 0 and 9 in python:\n```python\nfor i in range(10):\n    print(i)\n```",
                         "User: How to concatenate two dataframes?",
                         "Assistant: To concatenate two dataframes with the same columns you need to use the pandas.concat() method. Here's an example of how to use it:\n```python\nimport pandas as pd\n\n# create two dataframes with same columns\ndf1 = pd.DataFrame({'Id': [1, 2, 3], 'Name': ['John', 'Sam', 'Alice']})\ndf2 = pd.DataFrame({'Id': [4, 5, 6], 'Name': ['Dat', 'Kim', 'Jill']})\n\n# concatenate if value of column 'Id' is same\ndf3 = pd.concat([df1, df2], axis=0, ignore_index=True, sort=False)\n\n# view result\ndf3\n```\nThe output should look like this:\n| Id | Name |\n| --- | --- |\n| 1 | John |\n| 2 | Sam|\n| 3 | Alice |\n| 4 | Dat |\n| 5 | Kim|\n| 6 | Jill |\n*Note: This is just an example and there might be more sophisticated techniques to concatenate dataframes, depending on your problem."]

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
    "mood": mood + '\n',
    "warn_assistant": '\n' + warn_assistant + '\n',
    "starting_conversation": data.to_dict()
}

# Serializing json
json_object = json.dumps(dictionary, indent=4)
 
# Writing to file
file_name = setting_name.replace(' ', '_') + ".json"
with open(file_name, "w") as outfile:
    outfile.write(json_object)
    
print('Setting successfully created. You may close this window')