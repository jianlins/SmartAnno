import logging
from threading import Thread

from IPython.core.display import display, clear_output
from ipywidgets import widgets
from sqlalchemy import and_

from conf.ConfigReader import ConfigReader
from db.ORMs import Annotation
from gui.BranchingWidgets import RepeatHTMLToggleStep
from gui.Workflow import Step, logConsole
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
        self.ml_classifier.train(self.docs, [self.reviewed[doc.DOC_ID] for doc in self.docs])

    def backgroundTraining(self):
        thread_gm = Thread(target=self.initTraining)
        thread_gm.start()
        pass

    def init_real_time(self):
        self.loop_workflow.filters = self.workflow.filters
        self.readData()
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
                prediction = ReviewRBLoop.rb_classifier.classify(doc.TEXT, doc.DOC_NAME)
            repeat_step = ReviewML(description=content, options=self.workflow.types, value=prediction,
                                   js=self.js, master=self, reviewed=reviewed,
                                   button_style=('success' if reviewed else 'info'))
            self.appendRepeatStep(repeat_step)

        pass


class ReviewML(RepeatHTMLToggleStep):
    """A class for display and collect reviewers' annotation for a sample document/snippet"""

    def __init__(self, value=None, description='', options=[], tooltips=[],
                 branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None], js='', end_js='',
                 name=None, master=None, button_style='info', reviewed=False):
        self.master = master
        self.prediction = value
        self.reviewed = reviewed
        self.logger = logging.getLogger(__name__)
        self.progress = widgets.IntProgress(min=1, max=len(self.master.docs), value=1,
                                            layout=widgets.Layout(width='90%', height='14px'),
                                            style=dict(description_width='initial'))

        super().__init__(value=value, description=description, options=options, tooltips=tooltips,
                         branch_names=branch_names, branch_steps=branch_steps, js=js, end_js=end_js,
                         name=name, button_style=button_style)
        pass

    def start(self):
        """In running time, start to display a sample in the notebook output cell"""
        logConsole(('start step id/total steps', self.pos_id, len(self.workflow.steps)))
        if len(self.master.js) > 0:
            display(widgets.HTML(self.master.js))
        self.toggle.button_style = 'success'
        self.progress.value = self.pos_id + 1
        self.progress.description = 'Progress: ' + str(self.progress.value) + '/' + str(self.progress.max)
        clear_output(True)
        display(self.box)
        self.initNextDoc()
        pass

    def updateData(self, *args):
        """save the reviewed data"""
        self.data = self.toggle.value
        self.toggle.button_style = 'success'
        if self.reviewed:
            self.master.reviewed[self.master.docs[self.pos_id].DOC_ID] = self.toggle.value
            with self.master.workflow.dao.create_session() as session:
                logConsole(('update data:', self.pos_id, len(self.master.docs)))
                anno = session.query(Annotation).filter(
                    and_(Annotation.DOC_ID == self.master.docs[self.pos_id].DOC_ID,
                         Annotation.TASK_ID == self.master.workflow.task_id)).first()
                if anno is not None:
                    anno.REVIEWED_TYPE = self.toggle.value
                    anno.TYPE = self.prediction
                else:
                    anno = Annotation(TASK_ID=self.master.workflow.task_id,
                                      DOC_ID=self.master.docs[self.pos_id].DOC_ID,
                                      TYPE=self.prediction,
                                      REVIEWED_TYPE=self.toggle.value)
                    session.add(anno)
                self.master.annos[self.master.docs[self.pos_id].DOC_ID] = anno.clone()
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
        if self.master is None:
            return
        if self.next_step is None:
            if self.pos_id < len(self.master.docs) - 1:
                doc = self.master.docs[self.pos_id + 1]
                logConsole(('Initiate next doc', len(self.master.docs), 'current pos_id:', self.pos_id))
                content = self.master.genContent(doc)
                reviewed = False
                if doc.DOC_ID in self.master.annos and self.master.annos[doc.DOC_ID].REVIEWED_TYPE is not None:
                    prediction = self.master.annos[doc.DOC_ID].REVIEWED_TYPE
                    reviewed = True
                else:
                    prediction = ReviewRBLoop.rb_classifier.classify(doc.TEXT, doc.DOC_NAME)
                repeat_step = ReviewRB(description=content, options=self.master.workflow.types, value=prediction,
                                       js=self.js, master=self.master, reviewed=reviewed,
                                       button_style='success' if reviewed else 'info')
                self.master.appendRepeatStep(repeat_step)
            else:
                logConsole(('Initiate next step', len(self.master.docs), 'current pos_id:', self.pos_id,
                            'master\'s next step', self.master.next_step))
                self.next_step = self.master.next_step
                self.branch_buttons[1].linked_step = self.master.next_step
        pass

    def navigate(self, b):
        clear_output(True)
        self.updateData(b)
        logConsole(('navigate to b: ', b, hasattr(b, "linked_step")))
        logConsole(('navigate to branchbutton 1', hasattr(self.branch_buttons[1], 'linked_step'),
                    self.branch_buttons[1].linked_step))
        if hasattr(b, 'linked_step') and b.linked_step is not None:
            b.linked_step.start()
        else:
            if hasattr(self.branch_buttons[1], 'linked_step') and self.branch_buttons[1].linked_step is not None:
                self.branch_buttons[1].linked_step.start()
            elif not hasattr(b, 'navigate_direction') or b.navigate_direction == 1:
                self.complete()
            else:
                self.goBack()
        pass

    pass
