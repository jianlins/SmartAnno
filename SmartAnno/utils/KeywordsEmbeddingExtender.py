from collections import Set
from time import sleep

from IPython.core.display import clear_output, display
from ipywidgets import widgets

from gui.BranchingWidgets import LoopRepeatSteps, RepeatStep
from gui.MyWidgets import ToggleButtonsMultiSelectionInBox
from gui.Workflow import Step
from utils.GloveModel import GloveModel
from utils.KeywordsUMLSExtender import RepeatMultipleSelection
from utils.TreeSet import TreeSet


class KeywordsEmbeddingExtender(LoopRepeatSteps):
    """Extend word synonyms through word embedding"""
    description = "<h4>Closely related words to the keyword: '<b>%s</b>'</h4><p>Choose the ones that you want to include in keyword filters:</p>"
    max_query = 50

    def __init__(self, name=str(Step.global_id + 1), max_query=50):
        super().__init__([], name=name)
        KeywordsEmbeddingExtender.max_query = max_query
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
        self.workflow.we_extended = self.data

        super().complete()
        pass

    def init_real_time(self):
        word_dict = dict()
        self.loop_workflow.steps.clear()
        self.loop_workflow.extended = set()
        self.loop_workflow.filters = self.workflow.filters

        for type_name, words in self.workflow.to_we_ext_words.items():
            for word in words:
                word_dict[word] = type_name

        self.loop_workflow.to_ext_words = list(word_dict.items())
        word, type_name = self.loop_workflow.to_ext_words.pop(0)
        extended = GloveModel.glove_model.similar_by_word(word)
        extended = self.filterExtended(extended, type_name)
        self.loop_workflow.extended.update(extended)
        if len(extended) > 0:
            self.appendRepeatStep(
                RepeatWEMultipleSelection(description=KeywordsEmbeddingExtender.description % word,
                                          options=list(extended)))
        pass

    def filterExtended(self, extended, type_name):
        original_list = self.workflow.filters[type_name]
        filtered_list = set()
        for word in extended:
            if word in original_list or word in self.loop_workflow.extended:
                continue
            filtered_list.add(word)
        return filtered_list


class RepeatWEMultipleSelection(RepeatMultipleSelection):

    def initNextStepWhileReviewing(self):
        word, type_name = self.workflow.to_ext_words.pop(0)
        extended = GloveModel.glove_model.similar_by_word(word, KeywordsEmbeddingExtender.max_query)
        extended = self.filterExtended(extended, type_name)
        if len(extended) > 0:
            next_step = RepeatWEMultipleSelection(description=KeywordsEmbeddingExtender.description % word,
                                                  options=list(extended))
            next_step.setWorkflow(self.workflow)
            next_step.setPreviousStep(self.previous_step)
            next_step.setNextStep(self.next_step)
            self.setNextRepeat(next_step)
            next_step.setPreviousRepeat(self)
            self.workflow.steps.append(next_step)
        pass
