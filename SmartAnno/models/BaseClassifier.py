import abc
import joblib
import os

from SmartAnno.utils.NoteBookLogger import logMsg

NotTrained = 0
InTraining = 1
ReadyTrained = 2


class BaseClassifier:
    # indicate the status of classifier
    status = NotTrained
    instance = None

    # add optional paramters with default values here (will be overwritten by ___init__'s **kwargs)
    # These parameters will be shown in GUI ask for users' configuration

    def __init__(self, task_name='default_task', pipeline=None, params=None, model_file=None, **kwargs):
        self.task_name = task_name
        for name, value in kwargs.items():
            setattr(self, name, value)
        if model_file is None:
            model_file = 'models/saved/' + type(self).__name__ + '_' + task_name
        self.model_file = model_file
        self.model = None
        if os.path.isfile(self.model_file):
            self.model = self.loadModel()
            BaseClassifier.status = ReadyTrained
        else:
            self.model = self.init_model()
            BaseClassifier.status = NotTrained
        #  automatically set customized parameters to self object
        BaseClassifier.instance = self
        pass

    @abc.abstractmethod
    def init_model(self):
        """separate the definition, because at most of the time, you would want to automatically load previously trained
        model instead. """
        return None

    @abc.abstractmethod
    def classify(self, txt):
        return 'Irrelevant'

    @abc.abstractmethod
    def train(self, x, y):
        logMsg('error, abstract method called')
        # [] to return Documents, dict() to return grouping information
        pass

    def saveModel(self):
        """will be automatically saved when user click complete"""
        joblib.dump(self.model, self.model_file)
        pass

    def loadModel(self):
        """will be automatically load when initiate the classifier if self.model_file exists."""
        model = joblib.load(self.model_file)
        BaseClassifier.status = ReadyTrained
        return model
