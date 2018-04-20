from threading import Thread

from sqlalchemy import and_

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Annotation, Document
from SmartAnno.gui.Workflow import Step, logMsg
from SmartAnno.models.BaseClassifier import NotTrained, ReadyTrained
from SmartAnno.models.logistic.LogisticBOWClassifier import LogisticBOWClassifier
from SmartAnno.utils.NoteBookLogger import logError
from SmartAnno.utils.ReviewRBInit import ReviewRBInit
from SmartAnno.utils.ReviewRBLoop import ReviewRBLoop, ReviewRB


class ReviewMLLoop(ReviewRBLoop):
    """Review samples pre-annotated by machine learning model"""
    description = "<h4>%s</h4><p>Choose the correct type of this sample: </p><p>%s</p>"

    def __init__(self, name=str(Step.global_id + 1), ml_classifier_cls=LogisticBOWClassifier):
        # load class to use static variables to sync training status
        self.ml_classifier_cls = ml_classifier_cls
        # this is the actual classifier model, need to be initiated in ReviewMLInit step
        self.ml_classifier = None
        self.step_counter = 0
        self.learning_pace = None
        super().__init__(name)
        pass

    def start(self):
        """start displaying sample and annotation type options"""
        self.loop_workflow.steps = []
        self.init_real_time()
        # sleep(5)
        if len(self.loop_workflow.steps) > len(self.reviewed_docs):
            self.loop_workflow.steps[len(self.reviewed_docs)].start()
        else:
            print('You have finished all the reviews.')
            self.loop_workflow.steps[0].start()
        pass

    def readData(self):
        self.data = self.workflow.samples
        self.docs = self.data['docs']
        self.annos = self.data['annos']
        self.reviewed_docs = {doc_id: anno.REVIEWED_TYPE for doc_id, anno in self.annos.items() if
                              anno.REVIEWED_TYPE is not None}
        pass

    def initTraining(self):
        x = [doc.TEXT for doc in self.docs[:len(self.reviewed_docs)]]
        y = list(self.reviewed_docs.values())
        logMsg(('start ML training: ', type(self.ml_classifier), 'x=', len(x), 'y=', len(y)))
        self.ml_classifier.train(x, y)
        logMsg('training finished, start to predict...')
        self.initPrediction()

    def initPrediction(self):
        counter = 0
        with self.workflow.dao.create_session() as session:
            iter = session.query(Annotation, Document).join(Document, Document.DOC_ID == Annotation.DOC_ID).filter(
                and_(Annotation.TASK_ID == self.workflow.task_id, Annotation.REVIEWED_TYPE is None))
            for anno, doc in iter:
                if counter >= self.learning_pace * 1.5:
                    # don't need to process all the rest document for efficiency concerns
                    break
                logMsg(('predict doc: ', doc.DOC_ID, anno.TYPE))
                anno.TYPE = self.ml_classifier.classify(doc.TEXT)
                counter += 1
        counter = 0
        pass

    def backgroundTraining(self):
        """training the classifier in the backgraound"""
        thread_gm = Thread(target=self.initTraining)
        thread_gm.start()
        pass

    def init_real_time(self):
        self.ml_classifier = self.ml_classifier_cls(task_name=self.workflow.task_name)
        self.learning_pace = ConfigReader.getValue("review/ml_learning_pace")
        self.loop_workflow.filters = self.workflow.filters
        self.readData()
        if self.ml_classifier_cls.status == NotTrained:
            self.backgroundTraining()

        self.nlp = ReviewRBInit.nlp
        self.matcher = ReviewRBInit.matcher

        logMsg([doc.DOC_ID for doc in self.docs])
        if self.docs is not None and len(self.docs) > 0 and (
                self.loop_workflow is None or len(self.loop_workflow.steps) == 0):
            last_doc_pos = len(self.reviewed_docs) + 1 if len(self.reviewed_docs) < len(self.docs) else len(
                self.reviewed_docs)
            for i in range(0, last_doc_pos):
                doc = self.docs[i]
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
        self.step_counter += 1
        if self.step_counter >= self.learning_pace:
            if self.ml_classifier_cls.status == ReadyTrained:
                # reset counter
                self.step_counter = 0
                self.backgroundTraining()
                logMsg("Start retraining the ML model: " + str(self.ml_classifier))
            else:
                logMsg(
                    "ML model: " + str(self.ml_classifier) + " is not ready yet, postpone the re-training process.")
        res = None
        source = ''
        if doc.DOC_ID in self.annos:
            # if prediction has been made by previous model
            # just re-read from db to avoid thread conflict when manipulating lists, may improve later
            with self.workflow.dao.create_session() as session:
                anno_iter = session.query(Annotation).filter(
                    and_(Annotation.TASK_ID == self.workflow.task_id, Annotation.DOC_ID == doc.DOC_ID))
                for anno in anno_iter:
                    res = anno.TYPE
                    source = 'last classification'
                    break
        if res is None:
            if self.ml_classifier_cls.status == ReadyTrained:
                # if model is trained
                res = self.ml_classifier.classify(doc.TEXT)
                source = 'current classification'
            else:
                # try rule-based model as default
                res = ReviewRBLoop.rb_classifier.classify(doc.TEXT)
                source = 'rule-base classification'
        logMsg("Get classification from: " + source)
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
                logMsg(('Initiate next doc', len(self.master.docs), 'current pos_id:', self.pos_id))
                content = self.master.genContent(doc)
                reviewed = False
                if doc.DOC_ID in self.master.annos and self.master.annos[doc.DOC_ID].REVIEWED_TYPE is not None:
                    prediction = self.master.annos[doc.DOC_ID].REVIEWED_TYPE
                    logError(('reviewed: ', prediction))
                    reviewed = True
                else:
                    prediction = self.master.getPrediction(doc)
                    logError(('predicted: ', prediction))
                repeat_step = ReviewML(description=content, options=self.master.workflow.types, value=prediction,
                                       js=self.js, master=self.master, reviewed=reviewed,
                                       button_style='success' if reviewed else 'info')
                self.master.appendRepeatStep(repeat_step)
            else:
                logMsg(('Initiate next step', len(self.master.docs), 'current pos_id:', self.pos_id,
                        'master\'s next step', self.master.next_step))
                self.next_step = self.master.next_step
                self.branch_buttons[1].linked_step = self.master.next_step
        pass
