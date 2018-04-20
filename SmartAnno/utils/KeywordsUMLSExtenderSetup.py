from IPython.core.display import display
from ipywidgets import widgets, Label, Layout

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.gui.MyWidgets import ToggleButtonsMultiSelectionInBox
from SmartAnno.gui.PreviousNextWidgets import PreviousNext
from SmartAnno.utils.TreeSet import TreeSet


class KeywordsUMLSExtenderSetup(PreviousNext):
    def __init__(self,
                 description='<h4>Extend keywords through <b>UMLS</b></h4><p>Please select which keywords you want to '
                             'check the synonyms from UMLS:', name=None):
        self.api_key = ConfigReader.getValue('api_key')
        self.title = widgets.HTML(value=description)
        self.to_ext_words = dict()
        self.to_umls_ext_filters = dict()
        self.api_input = None
        super().__init__(name)

    def start(self):
        if self.workflow.api_key is None or len(self.workflow.api_key) < 5:
            self.workflow.steps[self.pos_id + 2].start()
            return
        if not hasattr(self.workflow, 'umls_extended'):
            self.workflow.umls_extended = dict()
        rows = self.showWords(self.workflow.filters)
        self.box = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        display(self.box)
        pass

    def showWords(self, filters):
        rows = [self.title]
        self.requestUMLSAPIKey(rows)
        for type_name in filters.keys():
            rows.append(Label(value=type_name + ':'))

            selections = ToggleButtonsMultiSelectionInBox(options=filters[type_name].to_list(),
                                                          value=list(self.to_ext_words[type_name]) if hasattr(self,
                                                                                                              'to_ext_words') and isinstance(
                                                              self.to_ext_words,
                                                              dict) and type_name in self.to_ext_words else [])
            self.to_umls_ext_filters[type_name] = selections
            rows.append(selections)
            rows += (self.addSeparator())
        rows += [self.addPreviousNext(self.show_previous, self.show_next)]
        return rows

    def complete(self):
        no_word_selected = True
        for type_name, toggle in self.to_umls_ext_filters.items():
            self.to_ext_words[type_name] = TreeSet(toggle.value)
            if no_word_selected and len(self.to_ext_words[type_name]) > 0:
                no_word_selected = False

        if not no_word_selected:
            self.workflow.to_ext_words = self.to_ext_words
            if self.api_key is None:
                self.api_key = self.api_input.value
                self.workflow.api_key = self.api_key
                ConfigReader.setValue("api_key", self.api_key)
                ConfigReader.saveConfig()
        else:
            self.setNextStep(self.workflow.steps[self.pos_id + 2])
            self.workflow.steps[self.pos_id + 2].setPreviousStep(self)
        super().complete()
        pass

    def requestUMLSAPIKey(self, rows):
        if self.api_key is not None or self.api_key.strip() != '':
            self.workflow.api_key = self.api_key
        else:
            rows.append(widgets.HTML(value='<h5>Set up your API key</h5><p>In order to use UMLS service, you will need '
                                           'to use a API key. Please type your API key below: (Here is '
                                           '<a href="https://documentation.uts.nlm.nih.gov/rest/authentication.html" '
                                           ' target="_blank">how to get a UMLS API key</a>)</p>'))
            self.api_input = widgets.Text(
                value='',
                placeholder='copy and paste your api key here',
                description='',
                disabled=False,
                layout=Layout(width='600')
            )
            rows.append(self.api_input)
            rows += self.addSeparator()
        pass
