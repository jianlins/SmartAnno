from IPython.core.display import display, clear_output
from ipywidgets import widgets, Label, Layout
from conf.ConfigReader import ConfigReader
from gui.MyWidgets import ToggleButtonsMultiSelection
from gui.PreviousNextWidgets import PreviousNext
from utils.TreeSet import TreeSet


class KeywordsEmbeddingExtenderSetup(PreviousNext):
    def __init__(self,
                 description='<h4>Extend keywords through Word Embedding</h4><p>Please select which keywords you want to '
                             'check the synonyms from the word embedding (currently only single word works for the word embedding model):',
                 name=None):

        self.title = widgets.HTML(value=description)
        self.to_we_ext_words = dict()
        self.to_we_ext_filters = dict()
        self.glove_path_input = None
        super().__init__(name)

    def start(self):
        clear_output()
        rows = self.showWords(self.workflow.filters)
        self.box = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        display(self.box)
        pass

    def showWords(self, filters):
        rows = [self.title]
        for type_name in filters.keys():
            rows.append(Label(value=type_name + ':'))
            # only show single word
            selections = ToggleButtonsMultiSelection(
                options=[word for word in filters[type_name].to_list() if ' ' not in word])
            self.to_we_ext_filters[type_name] = selections
            rows.append(selections)
            rows += (self.addSeparator())
        rows += [self.addPreviousNext(self.show_previous, self.show_next)]
        return rows

    def complete(self):
        no_word_selected = True
        for type_name, toggle in self.to_we_ext_filters.items():
            self.to_we_ext_words[type_name] = TreeSet(toggle.value)
            if no_word_selected and len(self.to_we_ext_words[type_name]) > 0:
                no_word_selected = False

        if not no_word_selected:
            self.workflow.to_we_ext_words = self.to_we_ext_words
            from utils.GloveModel import GloveModel
            from time import sleep
            if GloveModel.glove_model is None:
                print('Please wait for glove model to get ready.', end='', flush=True)
                while GloveModel.glove_model is None:
                    print('.', end='', flush=True)
                    sleep(1)
        else:
            self.setNextStep(self.workflow.steps[self.pos_id + 2])
            self.workflow.steps[self.pos_id + 2].setPreviousStep(self)
        super().complete()
        pass
