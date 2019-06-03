import logging
from collections import Counter

import numpy as np
from sklearn import metrics
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.svm import LinearSVC
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from SmartAnno.gui.Workflow import logMsg
from SmartAnno.models.BaseClassifier import BaseClassifier, InTraining, ReadyTrained, NotTrained

not_met_suffix = '_not_met'


class SVMBOWClassifier(BaseClassifier):
    # optional paramters with default values here (will be overwritten by ___init__'s **kwargs)
    # These parameters will be shown in GUI ask for users' configuration
    cv = 2
    workers = -1
    iterations = 3
    train_size = 0.8
    random_state = 777

    def __init__(self, task_name='default_task', pipeline=None, params=None, model_file=None, **kwargs):
        # generic parameters
        if params is None:
            self.params = {'vect__ngram_range': [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5)],
                           'tfidf__use_idf': (True, False),
                           'clf__C': (0.1, 0.5, 1.0, 5.0, 10.0, 50.0),
                           }
        else:
            self.params = params

        if pipeline is None:
            self.pipeline = Pipeline([('vect', CountVectorizer()),
                                      ('tfidf', TfidfTransformer()),
                                      ('clf', LinearSVC()),
                                      ])
        else:
            self.pipeline = pipeline
        super().__init__(task_name, pipeline, params, model_file, **kwargs)
        pass

    def init_model(self):
        model = RandomizedSearchCV(self.pipeline, param_distributions=self.params,
                                   n_iter=self.iterations,
                                   cv=self.cv,
                                   n_jobs=self.workers)
        # model=self.pipeline
        return model

    def train(self, x, y):
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
                                                                      stratify=y,
                                                                      train_size=self.train_size,
                                                                      random_state=self.random_state)
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
            print(
                'TRAIN data does not have enoguh examples (require {} cases) for all classes ({} cases) .  Skipping '
                'training for task : {}'.format(
                    self.cv, train_minority_instances, classname))
            return

        if test_minority_instances <= self.cv:
            logMsg(
                'TEST data does not have enoguh examples (require {} cases) for all classes ({} cases) .  Skipping '
                'training for task : {}'.format(
                    self.cv, train_minority_instances, classname))
            print(
                'TEST data does not have enoguh examples (require {} cases) for all classes ({} cases) .  Skipping '
                'training for task : {}'.format(
                    self.cv, train_minority_instances, classname))
            from time import sleep
            sleep(3)
            return

        # now we can train a model

        logMsg('Fitting model now for iterations = {}'.format(self.iterations))

        SVMBOWClassifier.status = InTraining
        self.model.fit(X_text_train, y_train)

        # print performances
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logMsg('Best params for the model : {}'.format(self.model.best_params_))

            logMsg('REPORT for TRAINING set and task : {}'.format(self.task_name))
            print(metrics.classification_report(y_train, self.model.predict(X_text_train),
                                                target_names=train_classes))

            logMsg('REPORT for TEST set and task : {}'.format(self.task_name))
            print(metrics.classification_report(y_test, self.model.predict(X_text_test),
                                                target_names=train_classes))
            SVMBOWClassifier.status = ReadyTrained

    pass

    def classify(self, txt):
        output = self.model.predict([txt])[0]
        return output
