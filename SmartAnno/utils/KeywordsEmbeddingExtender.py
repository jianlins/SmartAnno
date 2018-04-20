from SmartAnno.db.ORMs import Filter
from SmartAnno.gui.BranchingWidgets import LoopRepeatSteps
from SmartAnno.gui.Workflow import Step, logMsg
from SmartAnno.models.GloveModel import GloveModel
from SmartAnno.utils import KeywordsUMLSExtender
from SmartAnno.utils.KeywordsUMLSExtender import RepeatMultipleSelection
from SmartAnno.utils.TreeSet import TreeSet


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
        # Differentiate the keywords from where added----Not used for now
        # self.data = TreeSet()
        # for step in self.loop_workflow.steps:
        #     for word in step.data:
        #         self.data.add(word)
        # self.workflow.we_extended = self.data

        logMsg('update word embedding extended keywords into database')
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
        word_dict = dict()
        self.loop_workflow.steps.clear()
        self.loop_workflow.extended = set()

        for type_name, words in self.workflow.to_we_ext_words.items():
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
                extending = GloveModel.glove_model.similar_by_word(word.lower())
                extending = KeywordsUMLSExtender.filterExtended([pair[0] for pair in extending], type_name,
                                                                self.workflow.filters,
                                                                self.loop_workflow.extended)
            except KeyError:
                logMsg(("word '%s' not in vocabulary" % word.lower()))

            if len(extending) > 0:
                self.appendRepeatStep(
                    RepeatWEMultipleSelection(description=KeywordsEmbeddingExtender.description % word,
                                              options=list(extending), master=self, type_name=type_name))
            else:
                self.initiateRepeatStep()
        else:
            self.complete()


class RepeatWEMultipleSelection(RepeatMultipleSelection):

    def initNextStepWhileReviewing(self):
        if len(self.workflow.to_ext_words) > 0:
            word, type_name = self.workflow.to_ext_words.pop(0)
            extending = []
            try:
                extending = GloveModel.glove_model.similar_by_word(word.lower())
                extending = KeywordsUMLSExtender.filterExtended([pair[0] for pair in extending], type_name,
                                                                self.master.workflow.filters,
                                                                self.workflow.extended)
            except KeyError:
                logMsg(("word '%s' not in vocabulary" % word.lower()))

            if len(extending) > 0:
                next_step = RepeatWEMultipleSelection(description=KeywordsEmbeddingExtender.description % word,
                                                      options=list(extending), master=self.master,
                                                      type_name=type_name)
                next_step.setCompleteStep(self.branch_buttons[2].linked_step)
                self.workflow.append(next_step)
            else:
                self.initNextStepWhileReviewing()

        #
        # word, type_name = self.workflow.to_ext_words.pop(0)
        # extended = GloveModel.glove_model.similar_by_word(word, KeywordsEmbeddingExtender.max_query)
        # extended = self.filterExtended(extended, type_name)
        # if len(extended) > 0:
        #     next_step = RepeatWEMultipleSelection(description=KeywordsEmbeddingExtender.description % word,
        #                                           options=list(extended))
        #     next_step.setCompleteStep(self.branch_buttons[2].linked_step)
        #     self.workflow.append(next_step)
        pass
