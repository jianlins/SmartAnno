import logging
from threading import Thread

from IPython.core.display import display
from ipywidgets import widgets
from sqlalchemy import and_

from conf.ConfigReader import ConfigReader
from db.ORMs import Annotation
from gui.BranchingWidgets import RepeatHTMLToggleStep
from gui.Workflow import Step, logConsole
from models.BaseClassifier import BaseClassifier
from models.logistic.LogisticBOWClassifier import LogisticBOWClassifier
from utils.ReviewRBLoop import ReviewRBLoop


class ReviewMLLoop(ReviewRBLoop):
    """Review samples pre-annotated by machine learning model"""
    description = "<h4>%s</h4><p>Choose the correct type of this sample: </p><p>%s</p>"
    # how frequent to initiate a training process while reviewing (After # of newly reviewed samples)
    learning_pace = ConfigReader.getValue('log_model/learning_pace')

    def __init__(self, name=str(Step.global_id + 1), ml_classifier=LogisticBOWClassifier()):
        self.ml_classifier = ml_classifier
        super().__init__(name)
        pass

    def start(self):
        """start displaying sample and annotation type options"""
        self.loop_workflow.steps = []
        self.init_real_time()
        self.loop_workflow.start()
        pass

    def readData(self):
        self.data = self.workflow.steps[self.pos_id - 1].data
        self.docs = self.data['docs']
        self.reviewed = self.data['reviewed']
        self.if_contains = self.data['if_contains']
        self.annos = self.data['annos']

    def initTraining(self):
        self.ml_classifier.train(self.docs, self.annos)

    def backgroundTraining(self):
        thread_gm = Thread(target=self.initTraining)
        thread_gm.start()
        pass

    def init_real_time(self):
        self.loop_workflow.filters = self.workflow.filters
        self.readData()
        self.backgroundTraining()
        self.nlp = self.workflow.steps[self.pos_id - 1].nlp
        self.matcher = self.workflow.steps[self.pos_id - 1].matcher

        if self.docs is not None and len(self.docs) > 0 and (
                self.loop_workflow is None or len(self.loop_workflow.steps) == 0):
            doc = self.docs[0]
            content = self.genContent(doc)
            reviewed = False
            if doc.DOC_ID in self.annos and self.annos[doc.DOC_ID].REVIEWED_TYPE is not None:
                prediction = self.annos[doc.DOC_ID].REVIEWED_TYPE
                reviewed = True
            else:
                prediction = self.ml_classifier.classify(doc.TEXT, doc.DOC_NAME)
            repeat_step = ReviewML(description=content, options=self.workflow.types, value=prediction,
                                   js=self.js, loop_master=self, reviewed=reviewed,
                                   button_style=('success' if reviewed else 'info'))
            self.appendRepeatStep(repeat_step)

        pass


class ReviewML(RepeatHTMLToggleStep):
    """A class for display and collect reviewers' annotation for a sample document/snippet"""

    def __init__(self, value=None, description='', options=[], tooltips=[],
                 branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None], js='', end_js='',
                 name=None, loop_master=None, button_style='info', reviewed=False):
        self.loop_master = loop_master
        self.prediction = value
        self.reviewed = reviewed
        self.logger = logging.getLogger(__name__)
        self.progress = widgets.IntProgress(min=0, max=len(self.loop_master.docs), value=0,
                                            layout=widgets.Layout(width='90%', height='14px'),
                                            style=dict(description_width='initial'))

        super().__init__(value=value, description=description, options=options, tooltips=tooltips,
                         branch_names=branch_names, branch_steps=branch_steps, js=js, end_js=end_js,
                         name=name, button_style=button_style)
        pass

    def start(self):
        """In running time, start to display a sample in the notebook output cell"""
        logConsole(('start step id/total steps', self.pos_id, len(self.workflow.steps)))
        if len(self.loop_master.js) > 0:
            display(widgets.HTML(self.loop_master.js))
        self.progress.value = self.pos_id
        self.progress.description = 'Progress: ' + str(self.progress.value) + '/' + str(self.progress.max)
        display(self.box)
        logConsole(('self.pos_id:', self.pos_id, 'len(self.master.docs):', len(self.loop_master.docs),
                    'start init next step'))
        self.initNextDoc()
        pass

    def updateData(self,*args):
        """save the reviewed data"""
        self.data = self.toggle.value
        self.toggle.button_style = 'success'
        with self.loop_master.workflow.dao.create_session() as session:
            logConsole(('update data:', self.pos_id, len(self.loop_master.docs)))
            anno = session.query(Annotation).filter(
                and_(Annotation.DOC_ID == self.loop_master.docs[self.pos_id].DOC_ID,
                     Annotation.TASK_ID == self.loop_master.workflow.task_id)).first()
            if anno is not None:
                anno.REVIEWED_TYPE = self.toggle.value
                anno.TYPE = self.prediction
            else:
                session.add(Annotation(TASK_ID=self.loop_master.workflow.task_id,
                                       DOC_ID=self.loop_master.docs[self.pos_id].DOC_ID,
                                       TYPE=self.prediction,
                                       REVIEWED_TYPE=self.toggle.value))
        pass

    def createBox(self):
        rows = [self.progress, self.display_description, self.toggle] + \
               self.addSeparator(
                   top='10px') + self.addConditionsWidget()
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox

    def initNextDoc(self):
        """while displaying the current sample, prepare for the next sample"""
        if self.workflow is None:
            return
        if self.loop_master is None:
            return
        if self.pos_id + 1 >= len(self.loop_master.docs):
            return
        if self.next_step is None:
            doc = self.loop_master.docs[self.pos_id + 1]
            content = self.loop_master.genContent(doc)
            reviewed = False
            if doc.DOC_ID in self.loop_master.annos and self.loop_master.annos[doc.DOC_ID].REVIEWED_TYPE is not None:
                prediction = self.loop_master.annos[doc.DOC_ID].REVIEWED_TYPE
                reviewed = True
            else:
                prediction = self.loop_master.ml_classifier.classify(doc.TEXT, doc.DOC_NAME)
            repeat_step = ReviewML(description=content, options=self.loop_master.workflow.types, value=prediction,
                                   js=self.js, master=self.loop_master, reviewed=reviewed,
                                   button_style='success' if reviewed else 'info')
            self.loop_master.appendRepeatStep(repeat_step)
        pass

    pass
