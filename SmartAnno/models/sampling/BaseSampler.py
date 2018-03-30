import abc


class BaseSampler:
    def __init__(self, **kwargs):
        pass

    @abc.abstractmethod
    def sampling(self, sample_size=0):
        # [] to return Documents, dict() to return grouping information
        return [], dict()
