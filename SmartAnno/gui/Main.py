from IPython.core.display import display
from ipywidgets import widgets

from SmartAnno.gui.DirChooser import DirChooser
from SmartAnno.gui.FileIO import ReadFiles
# from SmartAnno.gui.SetFilterKeyWords import SetFilterKeyWords
from SmartAnno.gui.PreviousNextWidgets import PreviousNextHTML
from SmartAnno.gui.Workflow import Workflow
from SmartAnno.models.BaseClassifier import NotTrained
from SmartAnno.models.logistic.LogisticBOWClassifier import LogisticBOWClassifier
from SmartAnno.utils.AnnotationTypeDef import AnnotationTypeDef
from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.utils.DBInitiater import DBInitiater
from SmartAnno.utils.DataSetChooser import DataSetChooser
from SmartAnno.utils.DocsToDB import DocsToDB
from SmartAnno.utils.IntroStep import IntroStep
from SmartAnno.utils.KeywordsEmbeddingExtender import KeywordsEmbeddingExtender
from SmartAnno.utils.KeywordsEmbeddingExtenderSetup import KeywordsEmbeddingExtenderSetup
from SmartAnno.utils.KeywordsFiltering import KeywordsFiltering
from SmartAnno.utils.KeywordsUMLSExtender import KeywordsUMLSExtender
from SmartAnno.utils.KeywordsUMLSExtenderSetup import KeywordsUMLSExtenderSetup
from SmartAnno.utils.ReviewMLInit import ReviewMLInit
from SmartAnno.utils.ReviewMLLoop import ReviewMLLoop
from SmartAnno.utils.ReviewRBInit import ReviewRBInit
from SmartAnno.utils.ReviewRBLoop import ReviewRBLoop
from SmartAnno.utils.TaskChooser import TaskChooser


class Main:
    """Define and execute a workflow"""

    def __init__(self, ml_classifier_cls=LogisticBOWClassifier):

        self.data = None
        self.dir_chooser = None
        self.data = None
        self.status = NotTrained
        self.workflow = None
        self.ml_classifier_cls = ml_classifier_cls
        self.__setUpStage()
        pass

    def __setUpStage(self):
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
            [IntroStep(
                '<h2>Welcome to SmartAnno!</h2><h4>Do you want to start from beginning or continue previous reviewing? </h4>',
                name='intro'),
                DBInitiater(name='db_initiator'),
                DirChooser(name='choosedir'), ReadFiles(name='readfiles'),
                DocsToDB(name='save2db'),
                TaskChooser(name='tasknamer'),
                DataSetChooser(name='dataset_chooser', description='<h4>Choose which dateaset you want to use: </h4>'),

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
                ReviewMLLoop(name='ml_review', ml_classifier_cls=self.ml_classifier_cls),
                PreviousNextHTML(name='finish',
                                 description='<h3>Well done!</h3><h4>Now you have finished reviewing all the samples. ')
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

    def navigate(self):
        # TODO
        pass
