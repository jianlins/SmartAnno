import logging

from IPython.core.display import clear_output, display
from ipywidgets import widgets
from sqlalchemy import and_

from conf.ConfigReader import ConfigReader
from db.ORMs import Task, Annotation
from gui.BranchingWidgets import LoopRepeatSteps, RepeatHTMLToggleStep
from gui.Workflow import Step, logConsole
from models.rulebased.RBDocumentClassifier import RBDocumentClassifierFactory
from utils.InitLogger import InitLogger
from utils.TreeSet import TreeSet

InitLogger.initLogger()


class ReviewRBLoop(LoopRepeatSteps):
    """Extend word synonyms through word embedding"""
    description = "<h4>%s</h4><p>Choose the correct type of this sample: </p><p>%s</p>"
    rb_classifier = None

    def __init__(self, name=str(Step.global_id + 1)):
        self.docs = []
        self.data = dict()
        self.if_contains = dict()
        self.reviewed = dict()
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
        self.show_meta_name = ConfigReader().getValue("review/show_meta_name")
        super().__init__([], name=name)
        pass

    def start(self):
        self.init_real_time()
        self.loop_workflow.start()
        pass

    def backStart(self):
        self.loop_workflow.start(False)
        pass

    def complete(self):
        for i in range(0, len(self.docs)):
            doc = self.docs[i]
            self.reviewed[doc.DOC_ID] = self.loop_workflow.steps[i].data
        super().complete()
        pass

    def readData(self):
        self.data = self.workflow.steps[self.pos_id - 1].data
        self.docs = self.data['docs']
        self.if_contains = self.data['if_contains']

    def genContent(self, doc):
        html = "<h4>%s</h4>" % doc.DOC_NAME
        meta = self.genMetaTable(doc)
        div = self.genDiv(doc)
        return html + meta + div

    def genMetaTable(self, doc):
        headers = []
        values = []
        for meta_col in self.metaColumns:
            if self.show_meta_name:
                headers.append('<th>%s</th>' % meta_col)
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
        div = ''
        # div = '<button type="button" onclick="setFocusToTextBox()">Focus on next highlight</button>'
        div += '<div id="d1" style="overflow-y: scroll; height:400px;border:1px solid;border-color:#e5e8e8; ">'
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
                              + ' <span class="highlighter" style="background-color:  #7dcea0 ">' \
                              + spacy_doc[match[1]:match[2]].text + '</span> '
            pointer = match[2]
        highlight_text.append(spacy_doc[pointer:].text)
        highlight_text = ''.join(highlight_text).replace('\n', '<br/>')
        return highlight_text

    def init_real_time(self):
        ReviewRBLoop.rb_classifier = RBDocumentClassifierFactory.genDocumentClassifier(self.workflow.final_filters)
        self.loop_workflow.filters = self.workflow.filters
        self.readData()
        self.nlp = self.workflow.steps[self.pos_id - 1].nlp
        self.matcher = self.workflow.steps[self.pos_id - 1].matcher

        if self.docs is not None and len(self.docs) > 0 and (
                self.loop_workflow is None or len(self.loop_workflow.steps) == 0):
            doc = self.docs[0]
            content = self.genContent(doc)
            prediction = ReviewRBLoop.rb_classifier.classify(doc.TEXT, doc.DOC_NAME)
            repeat_step = ReviewRB(description=content, options=self.workflow.types, value=prediction,
                                   js=self.js, master=self)
            self.appendRepeatStep(repeat_step)

        pass


class ReviewRB(RepeatHTMLToggleStep):
    def __init__(self, value=None, description='', options=[], tooltips=[],
                 branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None], js='', end_js='',
                 name=None, master=None, button_style='info'):
        self.master = master
        self.prediction = value
        self.logger = logging.getLogger(__name__)
        self.progress = widgets.IntProgress(min=0, max=len(self.master.docs), value=0,
                                            layout=widgets.Layout(width='90%', height='14px'))

        super().__init__(value=value, description=description, options=options, tooltips=tooltips,
                         branch_names=branch_names, branch_steps=branch_steps, js=js, end_js=end_js,
                         name=name, button_style=button_style)
        pass

    def start(self):
        logConsole(('start step id/total steps', self.pos_id, len(self.workflow.steps)))
        if len(self.master.js) > 0:
            display(widgets.HTML(self.master.js))
        self.progress.value = self.pos_id
        self.progress.description = str(self.progress.value) + '/' + str(self.progress.max)
        display(self.box)
        logConsole(('self.pos_id:', self.pos_id, 'len(self.master.docs):', len(self.master.docs),
                   'start init next step'))
        self.initNextDoc()
        pass

    def updateData(self):
        self.data = self.toggle.value
        with self.master.workflow.dao.create_session() as session:
            logConsole(('update data:', self.pos_id, len(self.master.docs)))
            anno = session.query(Annotation).filter(
                and_(Annotation.DOC_ID == self.master.docs[self.pos_id].DOC_ID,
                     Annotation.TASK_ID == self.master.workflow.task_id)).first()
            if anno is not None:
                anno.REVIEWED_TYPE = self.toggle.value
                anno.TYPE = self.prediction
            else:
                session.add(Annotation(TASK_ID=self.master.workflow.task_id,
                                       DOC_ID=self.master.docs[self.pos_id].DOC_ID,
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
        if self.workflow is None:
            return
        if self.master is None:
            return
        if self.pos_id + 1 >= len(self.master.docs):
            return
        if self.next_step is None:
            doc = self.master.docs[self.pos_id + 1]
            content = self.master.genContent(doc)
            prediction = ReviewRBLoop.rb_classifier.classify(doc.TEXT, doc.DOC_NAME)
            repeat_step = ReviewRB(description=content, options=self.master.workflow.types, value=prediction,
                                   js=self.master.js, master=self.master)
            self.master.appendRepeatStep(repeat_step)
        pass

    pass
