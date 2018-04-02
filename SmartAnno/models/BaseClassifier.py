import abc


class BaseClassifier:
    # indicate the status of classifier
    ready = False

    classifier = None

    def __init__(self):
        pass

    @abc.abstractmethod
    def classify(self, txt):
        return 'neutral'

    @abc.abstractmethod
    def train(self, x, y):
        # [] to return Documents, dict() to return grouping information
        pass
