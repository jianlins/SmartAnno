import pytest
from SmartAnno.models.bert_sentimental.BERT_Sentimental import BERTSentimentalClassifier

from tensorflow import keras

import os
import re
import pandas as pd
import tensorflow as tf


# Load all files from a directory in a DataFrame.
def load_directory_data(directory):
    data = {}
    data["sentence"] = []
    data["sentiment"] = []
    for file_path in os.listdir(directory):
        with tf.gfile.GFile(os.path.join(directory, file_path), "r") as f:
            data["sentence"].append(f.read())
            data["sentiment"].append(re.match("\d+_(\d+)\.txt", file_path).group(1))
    return pd.DataFrame.from_dict(data)


# Merge positive and negative examples, add a polarity column and shuffle.
def load_dataset(directory):
    pos_df = load_directory_data(os.path.join(directory, "pos"))
    neg_df = load_directory_data(os.path.join(directory, "neg"))
    pos_df["polarity"] = 1
    neg_df["polarity"] = 0
    return pd.concat([pos_df, neg_df]).sample(frac=1).reset_index(drop=True)


# Download and process the dataset files.
def download_and_load_datasets(force_download=False):
    dataset = tf.keras.utils.get_file(
        fname="aclImdb.tar.gz",
        origin="http://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz",
        extract=True)

    train_df = load_dataset(os.path.join(os.path.dirname(dataset),
                                         "aclImdb", "train"))
    test_df = load_dataset(os.path.join(os.path.dirname(dataset),
                                        "aclImdb", "test"))

    return train_df, test_df


def get_x_y(data):
    x = []
    y = []
    for index, row in data.iterrows():
        x.append(row['sentence'])
        y.append(row['sentiment'])
    return x, y


train, test = download_and_load_datasets()
print(len(train), len(test))

bert_senti_cls = BERTSentimentalClassifier("bert_senti")

X_train, y_train = get_x_y(train)
# %%
bert_senti_cls.train(X_train[:5000], y_train[:5000])