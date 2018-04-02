import abc
from sklearn.externals import joblib
import os

NotTrained = 0
InTraining = 1
ReadyTrained = 2


class BaseClassifier:
    # indicate the status of classifier
    status = NotTrained
    model = None

    # add optional paramters with default values here (will be overwritten by ___init__'s **kwargs)
    # These parameters will be shown in GUI ask for users' configuration

    def __init__(self, task_name='default_task', pipeline=None, params=None, model_file=None, **kwargs):
        self.task_name = task_name
        if model_file is None:
            model_file = 'models/saved/' + str(type(self)) + '_' + task_name
        self.model_file = model_file
        if os.path.isfile(self.model_file):
            self.loadModel()
        else:
            self.defineModel()
        #  automatically set customized parameters to self object
        for name, value in kwargs.items():
            setattr(self, name, value)
        pass

    @abc.abstractmethod
    def defineModel(self):
        """separate the definition, because at most of the time, you would want to automatically load previously trained
        model instead. """
        BaseClassifier.status = NotTrained
        BaseClassifier.model = None
        pass

    @abc.abstractmethod
    def classify(self, txt):
        return 'neutral'

    @abc.abstractmethod
    def train(self, x, y):
        # [] to return Documents, dict() to return grouping information
        pass

    def saveModel(self):
        """will be automatically saved when user click complete"""
        joblib.dump(BaseClassifier.model, self.model_file)
        pass

    def loadModel(self):
        """will be automatically load when initiate the classifier if self.model_file exists."""
        BaseClassifier.model = joblib.load(self.model_file)
        BaseClassifier.status = ReadyTrained
        pass
