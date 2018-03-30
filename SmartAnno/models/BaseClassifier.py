import abc


class BaseClassifier:
    def __init__(self):
        pass

    @abc.abstractmethod
    def classify(self, txt):
        return 'neutral'
