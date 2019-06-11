import logging
from collections import Counter

import numpy as np
from SmartAnno.models.logistic import LogisticBOWClassifier
from sklearn import metrics
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub
from sklearn.pipeline import Pipeline

from SmartAnno.gui.Workflow import logMsg
from SmartAnno.models.BaseClassifier import BaseClassifier, InTraining, ReadyTrained, NotTrained

not_met_suffix = '_not_met'


class LogisticBOWClassifier(BaseClassifier):
    # optional paramters with default values here (will be overwritten by ___init__'s **kwargs)
    # These parameters will be shown in GUI ask for users' configuration
    cv = 2
    n_jobs = 1
    iterations = 2
    test_size = 0.3
    random_state = 777

    def __init__(self, task_name='default_task', pipeline=None, params=None, model_file=None, **kwargs):
        self.pipeline = pipeline
        super().__init__(task_name, pipeline, params, model_file, **kwargs)

        pass

    def init_model(self):
        if self.pipeline is None:
            self.pipeline = Pipeline([('vect', CountVectorizer()),
                                      ('clf', LogisticRegression(C=5.0, n_jobs=LogisticBOWClassifier.n_jobs)),
                                      ])
        return self.pipeline

    def train(self, x:list, y:list):
        logMsg('training...')

        stats = Counter(y)
        for classname, count in stats.items():
            if count < self.cv:
                logMsg(
                    'The whole annotated Data does not have enoguh examples for all classes.  Skipping training for '
                    'class : {}'.format(
                        classname))
                return

        # before we run a search, let's do an 80-20 split for (CV/Validation )
        # even if we do not have a lot of data to work with

        X_text_train, X_text_test, y_train, y_test = train_test_split(x, y,
                                                                      test_size=self.test_size,
                                                                      random_state=LogisticBOWClassifier.random_state)
        train_classes, train_y_indices = np.unique(y_train, return_inverse=True)
        test_classes, test_y_indices = np.unique(y_test, return_inverse=True)
        train_minority_instances = np.min(np.bincount(train_y_indices))
        test_minority_instances = np.min(np.bincount(train_y_indices))
        print('Train minority class instance count : {0}.  Test minority class instance count : {1}'.format(
            train_minority_instances,
            test_minority_instances))
        if train_minority_instances <= self.cv:
            logMsg(
                'TRAIN data does not have enoguh examples (require {} cases) for all classes ({} cases) .  Skipping '
                'training for task : {}'.format(
                    self.cv, train_minority_instances, classname))
            return

        if test_minority_instances <= self.cv:
            logMsg(
                'TEST data does not have enoguh examples (require {} cases) for all classes ({} cases) .  Skipping '
                'training for task : {}'.format(
                    self.cv, train_minority_instances, classname))
            return

        # now we can train a model

        logMsg('Fitting model now for iterations = {}'.format(self.iterations))

        LogisticBOWClassifier.status = InTraining
        self.model.fit(X_text_train, y_train)

        # print performances
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logMsg('REPORT for TRAINING set and task : {}'.format(self.task_name))
            print(metrics.classification_report(y_train, self.model.predict(X_text_train),
                                                target_names=train_classes))

            logMsg('REPORT for TEST set and task : {}'.format(self.task_name))
            print(metrics.classification_report(y_test, self.model.predict(X_text_test),
                                                target_names=train_classes))
        LogisticBOWClassifier.status = ReadyTrained

    pass

    def classify(self, txt):
        output = self.model.predict([txt])[0]
        return output
