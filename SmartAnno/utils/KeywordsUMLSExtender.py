from IPython.core.display import clear_output, display
from ipywidgets import widgets

from gui.BranchingWidgets import LoopRepeatSteps, RepeatStep
from gui.MyWidgets import ToggleButtonsMultiSelectionInBox
from gui.Workflow import Step
from umls.UMLSFinder import UMLSFinder
from utils.TreeSet import TreeSet


class KeywordsUMLSExtender(LoopRepeatSteps):
    umls = None
    description = "<h4>Synonyms of keyword '<b>%s</b>'</h4><p>Choose the ones that you want to include in keyword filters:</p>"

    def __init__(self, name=str(Step.global_id + 1), sources=['SNOMEDCT_US'], filter_by_length=0, max_query=30,
                 filter_by_contains=True):
        super().__init__([], name=name)
        self.sources = sources
        self.filter_by_length = filter_by_length
        self.filter_by_contains = filter_by_contains
        self.max_query = max_query
        pass

    def start(self):
        self.init_real_time()
        self.loop_workflow.start()
        pass

    def complete(self):
        self.data = TreeSet()
        for step in self.loop_workflow.steps:
            for word in step.data:
                self.data.add(word)
        self.workflow.umls_extended = self.data
        super().complete()
        pass

    def init_real_time(self):
        KeywordsUMLSExtender.umls = UMLSFinder(self.workflow.api_key, self.sources, self.filter_by_length,
                                               self.max_query,
                                               self.filter_by_contains)
        umls = KeywordsUMLSExtender.umls
        word_dict = dict()
        self.loop_workflow.filters = self.workflow.filters

        for type_name, words in self.workflow.to_ext_words.items():
            for word in words:
                word_dict[word] = type_name

        self.loop_workflow.to_ext_words = list(word_dict.items())
        word, type_name = self.loop_workflow.to_ext_words.pop(0)
        extended = umls.search(word)
        extended = self.filterExtended(extended, type_name)
        if len(extended) > 0:
            self.appendRepeatStep(
                RepeatMultipleSelection(description=KeywordsUMLSExtender.description % word,
                                        options=extended))
        pass

    def filterExtended(self, extended, type_name):
        original_list = self.workflow.filters[type_name]
        for word in original_list:
            if word in extended:
                extended.remove(word)
        return extended


class RepeatMultipleSelection(RepeatStep):
    def __init__(self, description='', options=[], tooltips=[],
                 branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None],
                 name=None):
        self.display_description = widgets.HTML(value=description)
        self.selections = ToggleButtonsMultiSelectionInBox(
            options=options, num_per_row=5
        )
        super().__init__(branch_names, branch_steps, name)
        pass

    def start(self):
        clear_output()
        self.box = self.updateBox()
        display(self.box)
        if len(self.workflow.to_ext_words) > 0:
            self.initNextStepWhileReviewing()
            pass

    def initNextStepWhileReviewing(self):
        word, type_name = self.workflow.to_ext_words.pop(0)
        extended = KeywordsUMLSExtender.umls.search(word)
        extended = self.filterExtended(extended, type_name)
        next_step = RepeatMultipleSelection(description=KeywordsUMLSExtender.description % word,
                                            options=extended)
        next_step.setWorkflow(self.workflow)
        next_step.setPreviousStep(self.previous_step)
        next_step.setNextStep(self.next_step)
        self.setNextRepeat(next_step)
        next_step.setPreviousRepeat(self)
        self.workflow.steps.append(next_step)
        pass

    def updateBox(self):
        rows = [self.display_description] + self.addSeparator(top='5px') + \
               [self.selections] + self.addSeparator(top='10px') + self.addConditions()
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox

    def navigate(self, b):
        # print(b)
        self.data = self.selections.value
        b.linked_step.start()
        pass

    def complete(self):
        self.data = self.selections.value
        super().complete()
        pass

    def filterExtended(self, extended, type_name):
        original_list = self.workflow.filters[type_name]
        for word in original_list:
            if word in extended:
                extended.remove(word)
        return extended
