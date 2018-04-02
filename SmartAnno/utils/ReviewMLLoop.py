from threading import Thread

from conf.ConfigReader import ConfigReader
from gui.Workflow import Step, logConsole
from models.BaseClassifier import NotTrained, ReadyTrained
from models.logistic.LogisticBOWClassifier import LogisticBOWClassifier
from utils.ReviewRBInit import ReviewRBInit
from utils.ReviewRBLoop import ReviewRBLoop, ReviewRB


class ReviewMLLoop(ReviewRBLoop):
    """Review samples pre-annotated by machine learning model"""
    description = "<h4>%s</h4><p>Choose the correct type of this sample: </p><p>%s</p>"
    # how frequent to initiate a training process while reviewing (After # of newly reviewed samples)
    learning_pace = ConfigReader.getValue('log_model/learning_pace')

    def __init__(self, name=str(Step.global_id + 1), ml_classifier_cls=LogisticBOWClassifier):
        # load class to use static variables to sync training status
        self.ml_classifier_cls = ml_classifier_cls
        # this is the actual classifier model, need to be initiated in ReviewMLInit step
        self.ml_classifier = ml_classifier_cls.model
        super().__init__(name)
        pass

    def start(self):
        """start displaying sample and annotation type options"""
        self.loop_workflow.steps = []
        self.init_real_time()
        self.loop_workflow.start()
        pass

    def readData(self):
        self.data = self.workflow.steps[self.pos_id - 2].data
        self.docs = self.data['docs']
        self.reviewed = self.data['reviewed']
        self.if_contains = self.data['if_contains']
        self.annos = self.data['annos']

    def initTraining(self):
        self.ml_classifier.train([doc.TEXT for doc in self.docs], [self.reviewed[doc.DOC_ID] for doc in self.docs])

    def backgroundTraining(self):
        """training the classifier in the backgraound"""
        thread_gm = Thread(target=self.initTraining)
        thread_gm.start()
        pass

    def init_real_time(self):
        self.loop_workflow.filters = self.workflow.filters
        self.readData()
        if self.ml_classifier_cls.status == NotTrained:
            self.backgroundTraining()

        self.nlp = ReviewRBInit.nlp
        self.matcher = ReviewRBInit.matcher

        if self.docs is not None and len(self.docs) > 0 and (
                self.loop_workflow is None or len(self.loop_workflow.steps) == 0):
            doc = self.docs[0]
            content = self.genContent(doc)
            reviewed = False
            if doc.DOC_ID in self.annos and self.annos[doc.DOC_ID].REVIEWED_TYPE is not None:
                prediction = self.annos[doc.DOC_ID].REVIEWED_TYPE
                reviewed = True
            else:
                prediction = self.getPrediction(doc)
            repeat_step = ReviewML(description=content, options=self.workflow.types, value=prediction,
                                   js=self.js, master=self, reviewed=reviewed,
                                   button_style=('success' if reviewed else 'info'))
            self.appendRepeatStep(repeat_step)

        pass

    def getPrediction(self, doc):
        """doc is an instance of db.ORMs.Document"""
        res = None
        if self.ml_classifier_cls.status == ReadyTrained:
            # if model is trained
            self.ml_classifier.classify(doc.TEXT)
        elif doc.DOC_ID in self.annos and self.annos[doc.DOC_ID].REVIEWED_TYPE is not None:
            # if prediction has been made by previous model
            res = self.annos[doc.DOC_ID].TYPE
        else:
            # try rule-based model as default
            res = ReviewRBLoop.rb_classifier.classify(doc.TEXT)
        return res


class ReviewML(ReviewRB):
    """A class for display and collect reviewers' annotation for a sample document/snippet"""

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
                    prediction = self.master.getPrediction(doc)
                repeat_step = ReviewML(description=content, options=self.master.workflow.types, value=prediction,
                                       js=self.js, master=self.master, reviewed=reviewed,
                                       button_style='success' if reviewed else 'info')
                self.master.appendRepeatStep(repeat_step)
            else:
                logConsole(('Initiate next step', len(self.master.docs), 'current pos_id:', self.pos_id,
                            'master\'s next step', self.master.next_step))
                self.next_step = self.master.next_step
                self.branch_buttons[1].linked_step = self.master.next_step
        pass

