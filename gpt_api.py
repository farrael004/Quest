from openai.embeddings_utils import get_embedding, cosine_similarity
import pandas as pd
from utils import api_error_warning
import openai


def find_top_similar_results(df: pd.DataFrame, query: str, n: int):
    if len(df.index) < n:
        n = len(df.index)
    embedding = create_embedding(query)
    df1 = df.copy()
    df1["similarities"] = df1["ada_search"].apply(lambda x: cosine_similarity(x, embedding))
    best_results = df1.sort_values("similarities", ascending=False).head(n)
    return best_results.drop(['similarities', 'ada_search'], axis=1).drop_duplicates(subset=['text'])


def create_embedding(query):
    try:
        return get_embedding(query, engine="text-embedding-ada-002")
    except:
        api_error_warning()


def gpt3_call(prompt: str, tokens: int, temperature: int=1, stop=None):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=tokens,
            n=1,
            stop=stop,
            temperature=temperature)

        return response["choices"][0]["text"].replace('\n', '  \n')
    except:
        api_error_warning()    