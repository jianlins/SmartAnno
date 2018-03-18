from IPython.core.display import display
from ipywidgets import widgets

from conf.ConfigReader import ConfigReader
from gui.ForkWidgets import IntroStep
from gui.PreviousNextWidgets import PreviousNextTextArea, PreviousNextLabel, PreviousNextHTML, PreviousNextIntSlider
from gui.DirChooser import DirChooser
from gui.FileIO import ReadFiles
# from gui.SetFilterKeyWords import SetFilterKeyWords
from gui.Workflow import Workflow
from utils.DocsToDB import DocsToDB


class GUI:
    """Define and execute a workflow"""

    def __init__(self):

        self.data = None
        self.dir_chooser = None
        self.data = None
        self.ready = False
        self.workflow = None
        self.setUpStage()

        pass

    def setUpStage(self):
        style = '''<style>.output_wrapper, .output {
                    height:auto !important;
                    max-height:1000px;  /* your desired max-height here */
                }
                .output_scroll {
                    box-shadow:none !important;
                    webkit-box-shadow:none !important;
                }
                </style>'''
        display(widgets.HTML(style))
        pass

    def start(self):
        self.workflow = Workflow(
            [IntroStep('<p><b>Welcome to SmartAnno!<br/>First let&apos;s import txt data from a directory. </p>'
                       '<br/>', name='intro'),
             DirChooser(name='choosedir'), ReadFiles(name='readfiles'),
             DocsToDB(name='save2db'),
             PreviousNextTextArea(
                 '<h4>Keywords Filter</h4><p>Type your keywords filter below. These key words are <b>optional</b>. They will'
                 ' be used to filter down the samples(documents or snippets). You can set how much percent'
                 'of the samples you want to review will be filter in <b>next step</b>. </p>'
                 '<p> This is helpful, if you estimate that '
                 'there will be too many samples with negative findings. </p>'
                 '<p>If not keywords is set, all the samples will be ask to reviewed. </p>', name='keywords'),
             PreviousNextIntSlider(value=60, min=0, max=100, step=10,
                                   description='<h4>Percentage to Filter: </h4><p>Choose how many percent of the samples '
                                               'you want to use the keywords filter.</p>', name='percent2filter'),
             PreviousNextTextArea(
                 '<h4>Annotation types:</h4><p>List all the types you want to identify below. Each type per line.<br/>If you'
                 'have too many types, try set up them separately, so that you won&apos;t need to choose from a long list '
                 'for each sample. </p>', name='types')
             ])
        self.workflow.start(False)
        pass

    def getData(self):
        return self.workflow.data

    def getLastStepData(self):
        length = len(self.workflow.data)
        if length > 0:
            return self.workflow.data[length - 1]
        else:
            return None
