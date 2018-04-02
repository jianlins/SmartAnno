import abc
from sklearn.externals import joblib
import os


class BaseClassifier:
    # indicate the status of classifier
    ready = False

    classifier = None

    def __init__(self, task_name='default_task', pipeline=None, params=None, model_file=None, **kwargs):
        self.task_name = task_name
        if model_file is None:
            model_file = 'models/saved/' + str(type(self)) + '_' + task_name
        self.model_file = model_file
        if os.path.isfile(self.model_file):
            self.loadModel()
        else:
            self.model = None
        pass

    @abc.abstractmethod
    def classify(self, txt):
        return 'neutral'

    @abc.abstractmethod
    def train(self, x, y):
        # [] to return Documents, dict() to return grouping information
        pass

    def saveModel(self):
        joblib.dump(self.model, self.model_file)
        pass

    def loadModel(self):
        self.model = joblib.load(self.model_file)
        pass
