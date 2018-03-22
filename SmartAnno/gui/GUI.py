from IPython.core.display import display
from ipywidgets import widgets

from gui.DirChooser import DirChooser
from gui.FileIO import ReadFiles
from gui.BranchingWidgets import IntroStep
from gui.PreviousNextWidgets import PreviousNextTextArea, PreviousNextIntSlider, PreviousNextText
# from gui.SetFilterKeyWords import SetFilterKeyWords
from gui.Workflow import Workflow
from utils.AnnotationTypeDef import AnnotationTypeDef
from utils.DBInitiater import DBInitiater
from utils.DocsToDB import DocsToDB
from utils.KeywordsFiltering import KeywordsFiltering
from utils.KeywordsUMLSExtender import KeywordsUMLSExtender
from utils.KeywordsUMLSExtenderSetup import KeywordsUMLSExtenderSetup
from utils.TaskChooser import TaskChooser


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
             DBInitiater(name='db_initiater'),
             TaskChooser(name='tasknamer'),
             DirChooser(name='choosedir'), ReadFiles(name='readfiles'),
             DocsToDB(name='save2db'),
             AnnotationTypeDef(
                 '<h4>Annotation types:</h4><p>List all the types you want to identify below. Each type per line.<br/>If you'
                 'have too many types, try set up them separately, so that you won&apos;t need to choose from a long list '
                 'for each sample. </p>', name='types'),
             KeywordsFiltering(
                 name='keywords'),
             PreviousNextIntSlider(value=60, min=0, max=100, step=10,
                                   description='<h4>Percentage to Filter: </h4><p>Choose how many percent of the samples '
                                               'you want to use the keywords filter.</p>', name='percent2filter'),
             KeywordsUMLSExtenderSetup(name='umls_extender_setup'),
             KeywordsUMLSExtender(name='umls_extender')
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
