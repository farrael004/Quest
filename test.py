import pickle
import pandas as pd
import openai
from openai.embeddings_utils import get_embedding, cosine_similarity

def load_google_history():
    # Try to find the search_history, if can't find it, create a new search_history
    try:
        with open('search_history.pickle', 'rb') as f:
            return pickle.load(f)
    except:
        data = pd.DataFrame(columns=['text', 'link', 'query', 'text_length', 'ada_search'])
        with open('search_history.pickle', 'wb') as f:
            pickle.dump(data, f)
        return data

def find_top_similar_results(df: pd.DataFrame, query: str, n: int):
    embedding = get_embedding(query, engine="text-embedding-ada-002")
    df1 = df.copy()
    df1["similarities"] = df1["ada_search"].apply(lambda x: cosine_similarity(x, embedding))
    df1 = df1.drop_duplicates(subset=['text'])
    best_results = df1.sort_values("similarities", ascending=False).head(n)
    return best_results.drop(['similarities', 'ada_search'], axis=1)

#google_results = load_google_history()
#google_results['text_length'] = google_results['text'].str.len()
#largest_results = google_results.nlargest(50, 'text_length')
#largest_results['ada_search'] = largest_results['text'].apply(lambda x: get_embedding(x, engine='text-embedding-ada-002'))
#largest_results.to_parquet('test_set.parket')
#print(largest_results)


google_results = pd.read_parquet('search_history.pickle')

similar_results = find_top_similar_results(google_results, 'Did elon musk buy Tesla?', 5)
print('\n\n'.join(similar_results['text'].to_list()))
print(list(set(similar_results['link'].to_list())))