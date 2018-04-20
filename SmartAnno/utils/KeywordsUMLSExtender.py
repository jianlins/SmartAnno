from IPython.core.display import display
from ipywidgets import widgets

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Filter
from SmartAnno.gui.BranchingWidgets import LoopRepeatSteps, RepeatStep
from SmartAnno.gui.MyWidgets import ToggleButtonsMultiSelectionInBox
from SmartAnno.gui.Workflow import Step, logMsg
from SmartAnno.umls.UMLSFinder import UMLSFinder


def filterExtended(extending, type_name, filters, extended):
    original_list = filters[type_name]
    filtered_list = set()
    for word in extending:
        if word in original_list or word in extended:
            continue
        filtered_list.add(word)
    extended.update(extended)
    return filtered_list


class KeywordsUMLSExtender(LoopRepeatSteps):
    umls = None
    description = "<h4>Synonyms of keyword '<b>%s</b>'</h4><p>Choose the ones that you want to include in keyword filters:</p>"

    def __init__(self, name=str(Step.global_id + 1), sources=['SNOMEDCT_US'], filter_by_length=0, max_query=50,
                 filter_by_contains=True):
        super().__init__([], name=name)
        self.sources = sources
        self.filter_by_length = filter_by_length
        self.filter_by_contains = filter_by_contains
        self.max_query = max_query
        self.loadDefaultConfig()
        pass

    def loadDefaultConfig(self):
        if self.sources is None or len(self.sources) == 0:
            self.sources = ['SNOMEDCT_US']
            ConfigReader.setValue("umls/sources", self.sources)
        if self.filter_by_length is None:
            self.filter_by_length = 0
            ConfigReader.setValue("umls/filter_by_length", 0)
        if self.filter_by_contains is None:
            self.filter_by_contains = True
            ConfigReader.setValue("umls/filter_by_contains", True)
        if self.max_query is None:
            self.max_query = 50
            ConfigReader.setValue("umls/max_query", 50)
        ConfigReader.saveConfig()
        pass

    def start(self):
        self.init_real_time()
        self.loop_workflow.start()
        pass

    def complete(self):
        # Differentiate the keywords from where added----Not used for now
        # self.data = TreeSet()
        # for step in self.loop_workflow.steps:
        #     for word in step.data:
        #         self.data.add(word)
        # self.workflow.umls_extended = self.data

        # update the keywords in db
        logMsg('update UMLS extended keywords into database')
        with self.workflow.dao.create_session() as session:
            records = session.query(Filter).filter(Filter.task_id == self.workflow.task_id) \
                .filter(Filter.type == 'orig')
            for record in records:
                type_name = record.type_name
                keywords = '\n'.join(self.workflow.filters[type_name]).strip()
                record.keyword = keywords
        super().complete()
        pass

    def init_real_time(self):
        KeywordsUMLSExtender.umls = UMLSFinder(self.workflow.api_key, self.sources, self.filter_by_length,
                                               self.max_query,
                                               self.filter_by_contains)
        word_dict = dict()
        self.loop_workflow.steps.clear()
        self.loop_workflow.filters = self.workflow.filters
        self.loop_workflow.extended = set()
        for type_name, words in self.workflow.to_ext_words.items():
            for word in words:
                word_dict[word] = type_name

        self.loop_workflow.to_ext_words = list(word_dict.items())
        self.initiateRepeatStep()
        pass

    def initiateRepeatStep(self):
        if len(self.loop_workflow.to_ext_words) > 0:
            word, type_name = self.loop_workflow.to_ext_words.pop(0)
            extending = []
            try:
                extending = KeywordsUMLSExtender.umls.search(word)
                # self.loop_workflow.extended saved all the extended words that will be displayed, no matter will be
                # selected or not, so that the same extended word won't be shown twice asking for selection
                extending = filterExtended(extending, type_name, self.workflow.filters, self.loop_workflow.extended)
            except KeyError:
                logMsg(("not synonym found for word '%s'" % word.lower()))

            if len(extending) > 0:
                self.appendRepeatStep(
                    RepeatMultipleSelection(description=KeywordsUMLSExtender.description % word,
                                            options=list(extending), master=self, type_name=type_name))
            else:
                self.initiateRepeatStep()
        else:
            self.complete()


class RepeatMultipleSelection(RepeatStep):
    def __init__(self, description='', options=[], tooltips=[],
                 branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None],
                 name=None, master=None, type_name='Irrelevant'):
        self.master = master
        self.type_name = type_name
        self.display_description = widgets.HTML(value=description)
        self.selections = ToggleButtonsMultiSelectionInBox(
            options=options, num_per_row=4
        )
        super().__init__(branch_names, branch_steps, name)
        pass

    def start(self):
        self.box = self.updateBox()
        display(self.box)
        if len(self.workflow.to_ext_words) > 0:
            self.initNextStepWhileReviewing()
            pass

    def initNextStepWhileReviewing(self):
        if len(self.workflow.to_ext_words) > 0:
            word, type_name = self.workflow.to_ext_words.pop(0)
            extended = KeywordsUMLSExtender.umls.search(word)
            extended = filterExtended(extended, type_name, self.master.workflow.filters, self.workflow.extended)
            if len(extended) > 0:
                next_step = RepeatMultipleSelection(description=KeywordsUMLSExtender.description % word,
                                                    options=list(extended), master=self.master, type_name=type_name)
                next_step.setCompleteStep(self.branch_buttons[2].linked_step)
                self.workflow.append(next_step)
            else:
                self.initNextStepWhileReviewing()
        pass

    def updateBox(self):
        rows = [self.display_description] + self.addSeparator(top='5px') + \
               [self.selections] + self.addSeparator(top='10px') + self.addConditionsWidget()
        vbox = widgets.VBox(rows, layout=widgets.Layout(width='100%', magins='10px'))
        return vbox

    def navigate(self, b):
        # print(b)
        self.data = self.selections.value
        if self.master is not None and self.data is not None:
            logMsg(self.data)
            self.master.workflow.filters[self.type_name].addAll(self.data)
        super().navigate(b)
        pass

    def complete(self):
        self.data = self.selections.value
        if self.master is not None and self.data is not None:
            self.master.workflow.filters[self.type_name].addAll(self.data)
        self.master.complete()
        pass
