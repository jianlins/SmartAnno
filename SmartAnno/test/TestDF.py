import pandas as pd


def addData(df):
    loc = len(df)
    df.loc[loc] = [5, 6]


df = pd.DataFrame([[1, 2], [3, 4]], columns=list('AB'))
addData(df)
print(df)

df['C'] = 5
print(df)
