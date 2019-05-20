import logging

from IPython.core.display import display, clear_output
from ipywidgets import widgets
from sqlalchemy import and_

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Annotation
from SmartAnno.gui.BranchingWidgets import LoopRepeatSteps, RepeatHTMLToggleStep
from SmartAnno.gui.Workflow import Step, logMsg
from SmartAnno.models.rulebased.RBDocumentClassifier import RBDocumentClassifierFactory
from SmartAnno.utils.ReviewRBInit import ReviewRBInit


class ReviewRBLoop(LoopRepeatSteps):
    """Review samples pre-annotated by rule-based model"""
    description = "<h4>%s</h4><p>Choose the correct type of this sample: </p><p>%s</p>"
    rb_classifier = None

    def __init__(self, name=str(Step.global_id + 1), **kwargs):
        super().__init__([], name=name)
        self.docs = []
        self.data = dict()
        self.annos = dict()
        self.reviewed_docs = dict()
        self.threshold = ConfigReader.getValue('review/rb_model_threshold')
        self.nlp = None
        self.js = '''<script>
function setFocusToTextBox(){
    var spans = document.getElementsByClassName("highlighter");
    var id=document.getElementById('d1').pos
    if (id===undefined){
      id=0
    }          
    if (id>=spans.length){
        id=0
    }
    var topPos = spans[id].offsetTop;    
    dv=document.getElementById('d1')
    dv.scrollTop = topPos-20;
    dv.pos=id+1;
}
</script>'''
        self.end_js = '''<script>document.getElementById('d1').pos=0;topPos=0;</script>'''
        self.matcher = None
        self.metaColumns = ConfigReader().getValue("review/meta_columns")
        self.div_height = ConfigReader().getValue("review/div_height")
        logMsg(('self.div_height:', self.div_height))
        self.show_meta_name = ConfigReader().getValue("review/show_meta_name")
        self.hightligh_span_tag = ' <span class="highlighter" style="background-color:  %s ">' % ConfigReader().getValue(
            "review/highlight_color")
        if 'rush_rule' in kwargs:
            self.rush_rule = kwargs['rush_rule']
        else:
            self.rush_rule = ConfigReader.getValue('rush_rules_path')

        pass

    def start(self):
        """start displaying sample and annotation type options"""
        self.loop_workflow.steps = []
        self.init_real_time()
        # self.loop_workflow.start()
        if len(self.loop_workflow.steps) > len(self.reviewed_docs):
            self.loop_workflow.steps[len(self.reviewed_docs)].start()
        else:
            # all the documents have been reviewed
            self.complete()
        pass

    def backStart(self):
        """if navigated from the next sample (the default should be from the previous sample)"""
        self.loop_workflow.start(False)
        pass

    def complete(self):
        super().complete()
        pass

    def readData(self):
        self.data = self.workflow.steps[self.pos_id - 1].data
        self.docs = self.data['docs']
        self.annos = self.data['annos']
        self.reviewed_docs = {doc_id: anno.REVIEWED_TYPE for doc_id, anno in self.annos.items() if
                              anno.REVIEWED_TYPE is not None}
        logMsg(('self.docs', len(self.docs)))
        logMsg(('self.annos', len(self.annos)))

    def genContent(self, doc):
        """display a sample (text content + metadata)"""
        meta = self.genMetaTable(doc)
        div = self.genDiv(doc)
        return meta + div

    def genMetaTable(self, doc):
        """display meta data"""
        headers = []
        values = []
        for meta_col in self.metaColumns:
            if self.show_meta_name:
                headers.append('<th>%s</th>' % meta_col)
            if meta_col == 'DOC_NAME':
                values.append('<td><b>%s</b></td>' % getattr(doc, meta_col))
            else:
                values.append('<td>%s</td>' % getattr(doc, meta_col))
        if len(values) > 0:
            meta = '<table style="width:100%">'
            if self.show_meta_name:
                meta += '<tr>%s</tr>' % (''.join(headers))
            meta += '<tr>%s</tr>' % (''.join(values))
            meta += '</table>'
        else:
            meta = ''
        return meta

    def genDiv(self, doc):
        """generate scrollable div to display the text content with keywords highlighted"""
        div = ''
        # div = '<button type="button" onclick="setFocusToTextBox()">Focus on next highlight</button>'
        div += '<div id="d1" style="overflow-y: scroll; height:' + self.div_height \
               + ';border:1px solid;border-color:#e5e8e8; ">'
        logMsg(('self.div_height:', self.div_height))
        spacy_doc = self.nlp(doc.TEXT)
        matches = self.matcher(spacy_doc)
        # consolePrint(matches)
        highlight_text = self.genHighlightTex(spacy_doc, matches)
        div += highlight_text + '</div>'
        return div

    def genHighlightTex(self, spacy_doc, matches):
        highlight_text = []
        pointer = 0
        for match in matches:
            highlight_text += spacy_doc[pointer:match[1]].text \
                              + self.hightligh_span_tag \
                              + spacy_doc[match[1]:match[2]].text + '</span> '
            pointer = match[2]
        highlight_text.append(spacy_doc[pointer:].text)
        highlight_text = ''.join(highlight_text).replace('\n', '<br/>')
        return highlight_text

    def init_real_time(self):
        ReviewRBLoop.rb_classifier = RBDocumentClassifierFactory.genDocumentClassifier(self.workflow.filters,
                                                                                       rush_rule=self.rush_rule)
        self.loop_workflow.filters = self.workflow.filters
        self.readData()
        self.nlp = ReviewRBInit.nlp
        self.matcher = ReviewRBInit.matcher
        if len(self.reviewed_docs) > self.threshold:
            self.complete()
            return

        if self.docs is not None and len(self.docs) > 0 and (
                self.loop_workflow is None or len(self.loop_workflow.steps) == 0):
            for i in range(0, len(self.reviewed_docs) + 1):
                doc = self.docs[i]
                content = self.genContent(doc)
                reviewed = False
                if doc.DOC_ID in self.annos and self.annos[doc.DOC_ID].REVIEWED_TYPE is not None:
                    prediction = self.annos[doc.DOC_ID].REVIEWED_TYPE
                    reviewed = True
                else:
                    prediction = ReviewRBLoop.rb_classifier.classify(doc.TEXT, doc.DOC_NAME)
                logMsg((i, doc.DOC_ID, reviewed))
                repeat_step = ReviewRB(description=content, options=self.workflow.types, value=prediction,
                                       js=self.js, master=self, reviewed=reviewed,
                                       button_style=('success' if reviewed else 'info'))
                self.appendRepeatStep(repeat_step)

        pass


class ReviewRB(RepeatHTMLToggleStep):
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
        logMsg(('start step id/total steps', self.pos_id, len(self.workflow.steps)))
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
            self.master.reviewed_docs[self.master.docs[self.pos_id].DOC_ID] = self.toggle.value
            with self.master.workflow.dao.create_session() as session:
                logMsg(('update data:', self.pos_id, len(self.master.docs)))
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
            # if reach the limit of rule-base preannotation max documents or the end of samples, jump to complete
            if self.pos_id < len(self.master.docs) - 1 and self.pos_id < self.master.threshold - 1:
                doc = self.master.docs[self.pos_id + 1]
                logMsg(('Initiate next doc', len(self.master.docs), 'current pos_id:', self.pos_id))
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
                logMsg(('Initiate next step', len(self.master.docs), 'current pos_id:', self.pos_id,
                        'master\'s next step', self.master.next_step))
                self.next_step = self.master.next_step
                self.branch_buttons[1].linked_step = self.master.next_step
        elif self.pos_id >= self.master.threshold - 1:
            self.navigate(self.branch_buttons[2])
        pass

    def navigate(self, b):
        clear_output(True)
        self.updateData(b)
        logMsg(('navigate to b: ', b, hasattr(b, "linked_step")))
        logMsg(('navigate to branchbutton 1', hasattr(self.branch_buttons[1], 'linked_step'),
                self.branch_buttons[1].linked_step))
        if hasattr(b, 'linked_step') and b.linked_step is not None:
            if b.description == 'Complete':
                self.master.complete()
            else:
                b.linked_step.start()
        else:
            if hasattr(self.branch_buttons[1], 'linked_step') and self.branch_buttons[1].linked_step is not None:
                self.branch_buttons[1].linked_step.start()
            elif not hasattr(b, 'navigate_direction') or b.navigate_direction == 1:
                logMsg('Button ' + str(b) + '\'s linked_step is not set. Assume complete the Repeat loop.')
                self.master.complete()
            else:
                self.goBack()
        pass

    pass
