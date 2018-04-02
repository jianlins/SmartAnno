from collections import OrderedDict


class LinkedHashSet(set):
    def __init__(self, collections):
        self.this_dict = OrderedDict(collections)
        pass

    def __contains__(self, item):
        return item in self.this_dict

    def add(self, item):
        self.this_dict[item] = None

    def remove(self, item):
        del self.this_dict[item]
