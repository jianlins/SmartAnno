from IPython.core.display import display
from ipywidgets import widgets

from conf.ConfigReader import ConfigReader
from gui.DirChooser import DirChooser
from gui.FileIO import ReadFiles
# from gui.SetFilterKeyWords import SetFilterKeyWords
from gui.PreviousNextWidgets import PreviousNextHTML
from gui.Workflow import Workflow
from models.BaseClassifier import NotTrained
from utils.AnnotationTypeDef import AnnotationTypeDef
from utils.DBInitiater import DBInitiater
from utils.DocsToDB import DocsToDB
from utils.IntroStep import IntroStep
from utils.KeywordsEmbeddingExtender import KeywordsEmbeddingExtender
from utils.KeywordsEmbeddingExtenderSetup import KeywordsEmbeddingExtenderSetup
from utils.KeywordsFiltering import KeywordsFiltering
from utils.KeywordsUMLSExtender import KeywordsUMLSExtender
from utils.KeywordsUMLSExtenderSetup import KeywordsUMLSExtenderSetup
from utils.ReviewMLInit import ReviewMLInit
from utils.ReviewMLLoop import ReviewMLLoop
from utils.ReviewRBInit import ReviewRBInit
from utils.ReviewRBLoop import ReviewRBLoop
from utils.TaskChooser import TaskChooser


class Main:
    """Define and execute a workflow"""

    def __init__(self):

        self.data = None
        self.dir_chooser = None
        self.data = None
        self.status = NotTrained
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
        cr = ConfigReader()
        self.workflow = Workflow(
            [IntroStep('<h2>Welcome to SmartAnno!</h2><h4>First, let&apos;s import txt data from a directory. </h4>',
                       name='intro'),
             DBInitiater(name='db_initiater'),
             TaskChooser(name='tasknamer'),
             DirChooser(name='choosedir'), ReadFiles(name='readfiles'),
             DocsToDB(name='save2db'),
             AnnotationTypeDef(
                 '<h3>Annotation types:</h3><p>List all the types you want to identify below. Each type per line.<br/>If you'
                 'have too many types, try set up them separately, so that you won&apos;t need to choose from a long list '
                 'for each sample. </p>', name='types'),
             KeywordsFiltering(
                 name='keywords'),
             # PreviousNextIntSlider(value=60, min=0, max=100, step=10,
             #                       description='<h4>Percentage to Filter: </h4><p>Choose how many percent of the samples '
             #                                   'you want to use the keywords filter.</p>', name='percent2filter'),
             KeywordsUMLSExtenderSetup(name='umls_extender_setup'),
             KeywordsUMLSExtender(name='umls_extender', sources=cr.getValue("umls/sources"),
                                  filter_by_length=cr.getValue("umls/filter_by_length"),
                                  filter_by_contains=cr.getValue("umls/filter_by_contains"),
                                  max_query=cr.getValue("umls/max_query")),
             KeywordsEmbeddingExtenderSetup(name='w_e_extender_setup'),
             KeywordsEmbeddingExtender(name='w_e_extender', max_query=40),
             ReviewRBInit(name="rb_review_init"),
             ReviewRBLoop(name='rb_review'),
             PreviousNextHTML(
                 description='<h2>Congratuations!</h2><h4>You have finished the initial review '
                             'on the rule-base preannotations. </h4>',
                 name='rb_review_done'),
             ReviewMLInit(name='ml_review_init'),
             ReviewMLLoop(name='ml_review')
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