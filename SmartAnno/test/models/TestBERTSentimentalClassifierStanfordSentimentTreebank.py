import os
from collections import OrderedDict

import numpy as np
import pandas as pd
import tensorflow as tf

from SmartAnno.models.bert_sentimental.BERTSentClassifier import BERTSentClassifier


# Merge positive and negative examples, add a polarity column and shuffle.
def load_dataset(zipped_file: str):
    from zipfile import ZipFile
    label_data = OrderedDict()
    sentence_data = {}
    print(zipped_file)
    with ZipFile(zipped_file) as myzip:
        with myzip.open('stanfordSentimentTreebank/sentiment_labels.txt') as labels:
            for line in labels:
                line = line.decode('utf-8')
                if len(line) > 0 and line[0].isdigit():
                    row = line.split('|')
                    value = float(row[1])
                    # categorize the labels
                    label = 'neu'
                    if value <= 0.4:
                        label = 'neg'
                    elif value > 0.6:
                        label = 'pos'
                    label_data[int(row[0])] = label
        with myzip.open('stanfordSentimentTreebank/dictionary.txt') as sentences:
            for line in sentences:
                line = line.decode('utf-8')
                if len(line) > 0:
                    row = line.split('|')
                    sentence_data[int(row[1])] = row[0]
    data = {}
    for id, label in label_data.items():
        data[id] = [sentence_data[id], label]
    return pd.DataFrame.from_dict(data, orient='index', columns=['sentence', 'sentiment'])


# Download and process the dataset files.
def download_and_load_datasets(force_download=False, test_size=0.33, random_state=777):
    dataset = tf.keras.utils.get_file(
        fname="stanfordSentimentTreebank.zip",
        origin="https://nlp.stanford.edu/~socherr/stanfordSentimentTreebank.zip",
        extract=False)

    df = load_dataset(os.path.join(os.path.dirname(dataset),
                                   "stanfordSentimentTreebank.zip"))
    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
    return train_df, test_df


def get_x_y(data: pd.DataFrame) -> (np.ndarray, np.ndarray):
    return data['sentence'].values, data['sentiment'].values


train, test = download_and_load_datasets()
print(len(train), len(test))
# %%
bert_senti_cls = BERTSentClassifier("stanford_senti")

X_train, y_train = get_x_y(train[:100])

bert_senti_cls.train(X_train, y_train)

# %%

pred_sentences = [
    "That movie was absolutely awful",
    "The acting was a bit lacking",
    "The film was creative and surprising",
    "Absolutely fantastic!"
]
predictions = bert_senti_cls.predict(pred_sentences)

print(predictions)

# %%

print(bert_senti_cls.classify('This is a good game.'))
