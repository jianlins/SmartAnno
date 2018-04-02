import logging
import sys
import os
import getpass
import xml.etree.ElementTree as ET
import numpy as np
import sklearn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn import metrics
from sklearn.model_selection import train_test_split
from collections import Counter
import nltk
import gensim
from optparse import OptionParser

from conf.ConfigReader import ConfigReader
from gui.Workflow import logConsole
from models.BaseClassifier import BaseClassifier

not_met_suffix = '_not_met'


class LogisticBOWClassifier(BaseClassifier):

    def __init__(self, pipeline=None, params=None):
        if params is None:
            self.params = {'vect__ngram_range': [(1, 1), (1, 2), (1, 3)],
                           'tfidf__use_idf': (True, False),
                           'clf__C': (0.1, 0.5, 1.0, 5.0, 10.0, 50.0),
                           }
        else:
            self.params = params

        if pipeline is None:
            self.pipeline = Pipeline([('vect', CountVectorizer()),
                                      ('tfidf', TfidfTransformer()),
                                      ('clf', LogisticRegression()),
                                      ])
        else:
            self.pipeline = pipeline
        self.rs = None
        pass

    def train(self, x, y, class_names, task_name, workers=-1, cv=4, iterations=1, train_size=0.8, random_state=777):
        LogisticBOWClassifier.ready = False
        stats = Counter(y)
        for classname, count in stats.items():
            if count < cv:
                logConsole(
                    'TEST data does not have enoguh examples for all classes.  Skipping training for class : {}'.format(
                        classname))
                return

        # before we run a search, let's do an 80-20 split for (CV/Validation )
        # even if we do not have a lot of data to work with
        X_text_train, X_text_test, y_train, y_test = train_test_split(x, y,
                                                                      stratify=y,
                                                                      train_size=train_size,
                                                                      random_state=random_state)
        train_classes, train_y_indices = np.unique(y_train, return_inverse=True)
        test_classes, test_y_indices = np.unique(y_test, return_inverse=True)
        train_minority_instances = np.min(np.bincount(train_y_indices))
        test_minority_instances = np.min(np.bincount(train_y_indices))
        print('Train minority class instance count : {0}.  Test minority class instance count : {1}'.format(
            train_minority_instances,
            test_minority_instances))
        if train_minority_instances <= cv:
            logConsole(
                'TRAIN data does not have enoguh examples for all classes.  Skipping training for class : {}'.format(
                    classname))
            return

        if test_minority_instances <= cv:
            logConsole(
                'TEST data does not have enoguh examples for all classes.  Skipping training for class : {}'.format(
                    classname))
            return

        # now we can train a model
        self.rs = RandomizedSearchCV(self.pipeline, param_distributions=self.params,
                                     n_iter=iterations,
                                     cv=cv,
                                     n_jobs=workers)

        logConsole('Fitting model now for iterations = {}'.format(iterations))
        self.rs.fit(X_text_train, y_train)

        # print performances
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            print('Best params for the model : {}'.format(self.rs.best_params_))

            print('REPORT for TRAINING set and task : {}'.format(task_name))
            print(metrics.classification_report(y_train, self.rs.predict(X_text_train),
                                                target_names=class_names))

            print('REPORT for TEST set and task : {}'.format(task_name))
            print(metrics.classification_report(y_test, self.rs.predict(X_text_test),
                                                target_names=class_names))
        LogisticBOWClassifier.ready = True

    pass

    def classify(self, txt):
        output = ''
        output = self.rs.predict([txt])[0]
        return output
