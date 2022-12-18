import pickle
import pandas as pd
import openai
import json
import os
from openai.embeddings_utils import get_embedding, cosine_similarity

# Navigate to the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
with open(os.path.join(parent_dir, 'api_key.txt'), 'r') as f:
    openai.api_key = f.read()


def load_google_history():
    # Load the JSON file
    with open('Strictly_Factual.json', 'r') as f:
        return json.load(f)

def find_top_similar_results(df: pd.DataFrame, query: str, n: int):
    embedding = get_embedding(query, engine="text-embedding-ada-002")
    df1 = df.copy()
    df1["similarities"] = df1["ada_search"].apply(lambda x: cosine_similarity(x, embedding))
    df1 = df1.drop_duplicates(subset=['text'])
    best_results = df1.sort_values("similarities", ascending=False).head(n)
    return best_results.drop(['similarities', 'ada_search'], axis=1)


settings = dict(load_google_history())
google_results = pd.DataFrame(settings['starting_conversation'])

similar_results = find_top_similar_results(google_results, 'Did elon musk buy Tesla?', 3)
print('\n'.join(similar_results['text'].to_list()))