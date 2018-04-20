from threading import Thread

from IPython.core.display import clear_output, display
from ipywidgets import widgets

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.gui.BranchingWidgets import BranchingStep
from SmartAnno.models.GloveModel import GloveModel


class IntroStep(BranchingStep):
    def __init__(self, description='', name=None):
        self.glove_path = ConfigReader.getValue('glove/model_path')
        self.glove_vocab = ConfigReader.getValue('glove/vocab')
        self.glove_vector = ConfigReader.getValue('glove/vector')
        # widgets to take the user inputs
        self.glove_path_input = None
        self.glove_vocab_input = None
        self.glove_vector_input = None
        self.api_key_input = None

        if self.glove_vocab is None:
            self.glove_vocab = 1900000

        if self.glove_vector is None:
            self.glove_vector = 300
        self.html = widgets.HTML(value=description)
        super().__init__(name)
        pass

    def start(self):
        self.branch_buttons = [widgets.Button(description=d, layout=widgets.Layout(width='150px', left='100px')) for d
                               in
                               ['StartOver', 'ContinueReviewing']]
        clear_output()
        self.box = self.createBox()
        display(self.box)
        pass

    def navigate(self, button):
        if self.glove_path_input is not None:
            self.saveGloveConfig()
        if self.api_key_input is not None:
            self.saveAPIKey()
        else:
            self.workflow.api_key = ConfigReader.getValue("api_key")
        self.backgroundWork()
        if button.description == 'ContinueReviewing':
            self.workflow.to_continue = True
            self.workflow.steps[1].start()
            self.workflow.steps[1].complete()
        else:
            self.workflow.to_continue = False
            self.workflow.steps[1].start()
        pass

    def complete(self):
        self.navigate(self.branch_buttons[0])
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

    def saveAPIKey(self):
        ConfigReader.setValue("api_key", self.api_key_input.value)
        ConfigReader.saveConfig()
        self.workflow.api_key = self.api_key_input.value
        pass

    def createBox(self):
        rows = self.addSeparator()
        rows += [self.html]
        self.requestWELocation(rows)
        self.requestUMLSAPIKey(rows)
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
        if self.glove_path is None or len(self.glove_path.strip()) == 0:
            rows += self.addSeparator()
            rows.append(
                widgets.HTML(value='<h4>Set up your Glove model</h4><p>In order to use word embedding, you need '
                                   'to tell where the glove model locates:</p><p>If you have not downloaded yet,'
                                   'you can download it from <a href="https://nlp.stanford.edu/projects/glove/" '
                                   ' target="_blank">Glove Site</a><p>. Once you download it, you need to unzip it'
                                   ' and copy the unzipped file path here. SmartAnno will automatically convert it '
                                   'into binary format (will be loaded faster). If you do not set it up, the word '
                                   'embedding synonym extender will be <b>skipped</b>.</p>'))
            self.glove_path_input = widgets.Text(
                value='',
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
                widgets.HTML(
                    value='<h4>Set your API Key</h4><p>In order to use the UMLS synonym checking module, you need to set'
                          ' up your API key: (<a href="https://www.nlm.nih.gov/research/umls/user_education/quick_tours/'
                          'UTS-API/UTS_REST_API_Authentication.html" target="_blank">How to get your API Key_at 01:12 from'
                          ' beginning. </a>)</p><p>If you do not set the api key, the UMLS synonym extender will be '
                          '<b>skipped</b>.</p>'))
            self.api_key_input = widgets.Text(value='',
                                              placeholder='',
                                              description='', disabled=False)
            rows.append(self.api_key_input)
            rows += self.addSeparator()
