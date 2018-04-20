from threading import Thread

from IPython.core.display import clear_output, display
from ipywidgets import widgets

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.gui.PreviousNextWidgets import PreviousNext
from SmartAnno.models.GloveModel import GloveModel


class Setup(PreviousNext):
    def __init__(self, name=None):
        ConfigReader()
        self.glove_path = ConfigReader.getValue('glove/model_path')
        self.glove_vocab = ConfigReader.getValue('glove/vocab')
        self.glove_vector = ConfigReader.getValue('glove/vector')
        # widgets to take the user inputs
        self.glove_path_input = None
        self.glove_vocab_input = None
        self.api_key_input = None
        self.glove_vector_input = None

        if self.glove_vocab is None:
            self.glove_vocab = 1900000

        if self.glove_vector is None:
            self.glove_vector = 300
        super().__init__(name)
        pass

    def start(self):
        clear_output()
        self.box = self.createBox()
        display(self.box)
        pass

    def saveGloveConfig(self):
        self.glove_path = self.glove_path_input.value
        self.glove_vocab = self.glove_vocab_input.value
        self.glove_vector = self.glove_vector_input.value
        self.workflow.glove_path = self.glove_path
        ConfigReader.setValue("glove/vocab", int(self.glove_vocab))
        ConfigReader.setValue("glove/vector", int(self.glove_vector))
        ConfigReader.setValue("glove/model_path", self.glove_path)
        ConfigReader.saveConfig()
        pass

    def createBox(self):
        rows = []
        self.requestWELocation(rows)
        rows += self.addSeparator() + self.addConditions()
        # print('\n'.join([str(row) for row in rows]))
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def addConditions(self):
        for button in self.branch_buttons:
            button.on_click(self.navigate)
        return [widgets.HBox(self.branch_buttons, layout=widgets.Layout(left='10%', width='80%'))]

    def backgroundWork(self):
        thread_gm = Thread(target=self.prepareGloveModel)
        thread_gm.start()
        pass

    def prepareGloveModel(self):
        GloveModel(word2vec_file=self.glove_path, vocab=self.glove_vocab, vect=self.glove_vector)
        pass

    def requestWELocation(self, rows):
        if self.glove_path is None or self.glove_path.strip() == '':
            rows += self.addSeparator()
            rows.append(
                widgets.HTML(value='<h4>Set up your Glove model</h4><p>In order to use word embedding, you need '
                                   'to tell where the glove model locates:</p>'))
            self.glove_path_input = widgets.Text(
                value='models/saved/glove/glove.42B.300d.bin',
                placeholder='copy and paste your glove model file location here',
                description='',
                disabled=False,
                layout=widgets.Layout(width='70%')
            )

            self.glove_vocab_input = widgets.Text(value=str(self.glove_vocab),
                                                  placeholder='',
                                                  description='', disabled=False)
            self.glove_vector_input = widgets.Text(value=str(self.glove_vector),
                                                   placeholder='the vector size of the glove model',
                                                   description='', disabled=False)
            rows.append(self.glove_path_input)
            rows.append(widgets.HTML(value='The vocabulary size of the glove model:'))
            rows.append(self.glove_vocab_input)
            rows.append(widgets.HTML(value='The vector size of the glove model:'))
            rows.append(self.glove_vector_input)
            rows += self.addSeparator()
        pass

    def requestUMLSAPIKey(self, rows):
        api_key = ConfigReader.getValue("api_key")
        if api_key is None or len(api_key) == 0:
            rows.append(
                widgets.HTML(value='<h4>Set up your Glove model</h4><p>In order to use word embedding, you need '
                                   'to tell where the glove model locates:</p>'))
            self.api_key_input = widgets.Text(value='',
                                              placeholder='',
                                              description='', disabled=False)
            rows.append(self.api_key_input)
            rows += self.addSeparator()
