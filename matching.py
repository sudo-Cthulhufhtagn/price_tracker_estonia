from fuzzywuzzy import process, fuzz
import pandas as pd

rimi = pd.read_csv('rimi.csv')
selver = pd.read_csv('selver.csv')

guesses = []
similarity = []
ratio = []
for i in rimi.name:
    ratio = process.extract( i, selver.name, limit=1, scorer=fuzz.token_sort_ratio)
    guesses.append(ratio[0][0])
    similarity.append(ratio[0][1])

rimi['selver_guess'] = pd.Series(guesses)
rimi['selver_price'] = rimi['selver_guess'].apply(lambda x: selver.loc[selver.name == x].price.values[0])
rimi['selver_price_kg'] = rimi['selver_guess'].apply(lambda x: selver.loc[selver.name == x]['price/kg'].values[0])
rimi['similarity'] = pd.Series(similarity)

rimi = rimi[[
            'id',
            'name',
            'selver_guess',
            'price',
            'selver_price',
            'price/kg',
            'selver_price_kg',
            'similarity'
]]

rimi = rimi.sort_values('similarity', ascending=False)

rimi.to_csv('compared.csv')