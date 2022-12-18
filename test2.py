import pandas as pd


df1 = pd.read_parquet('history1_test.parquet')
df2 = pd.read_parquet('results1_test.parquet')
df3 = pd.read_parquet('history2_test.parquet')
df4 = pd.read_parquet('results2_test.parquet')

# Concatenate the dataframes
df_concat = pd.concat([df3, df4]).drop_duplicates(subset=['text'])
print(df_concat)
