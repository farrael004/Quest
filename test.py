import pickle
import pandas as pd
from openai.embeddings_utils import get_embedding, cosine_similarity

def load_google_history():
    # Try to find the search_history, if can't find it, create a new search_history
    try:
        with open('search_history.pickle', 'rb') as f:
            return pickle.load(f)
    except:
        data = pd.DataFrame(columns=['text', 'link', 'query'])
        with open('search_history.pickle', 'wb') as f:
            pickle.dump(data, f)
        return data
    
google_results = load_google_history()
#google_results['ada_search'] = google_results['text'].apply(lambda x: get_embedding(x, engine='text-embedding-ada-002'))
print(google_results)