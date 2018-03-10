from os import path

from IPython.core.display import display, HTML, clear_output
from gensim.models import KeyedVectors
from collections import Set

from gui.CustomWidgets import TimerProgressBar, OptionButtons
from gui.Workflow import Step


class SetFilterKeyWords(Step):
	"""Set up keywords to narrow the documents/snippets that need to be annotated/reviewed.
	You can set if use 100% filtering(all documents/snippets must have one of the keywords you setup),
	or a proportion of documents/snippets will apply that constrain (the rest will randomly pulled from the corpus)"""

	def __init__(self, intro_wait=4):
		self.glove_model = None
		self.intro_wait = intro_wait
		self.resetParameters()
		self.umls_rest = None
		pass

	def resetParameters(self):
		self.words = []
		self.words_set = dict()
		pass

	def start(self):
		self.showIntructions()
		pass

	def showIntructions(self):
		display(HTML("<h4>Set up keywords filters:</h4><p>If you need to narrow down your scope of the documents for annotation, you will want"
					 "to use a list of keywords to filter out the documents that don't have any of these keywords.</p>"
					 "<p>We will work you through the process. </p>"))
		next_cancel = OptionButtons(options=['next', 'cancel'], description='',
									tooltips=['next: Start configuring keywords', 'cancle: won\'t use keywords filter, use all data instead'])
		clear_output(wait=True)
		next_cancel.setOpitionalNextSteps([self.chooseIfUseUMLS(), self.complete()])
		pass

	def chooseIfUseUMLS(self):
		display(HTML("<h4>Use UMLS heuristics:</h4>"
					 "<p>Use UMLS resources to expand your keywords through finding synonyms, hypernyms or hyponyms. </p>"
					 "<p>You will need UMLS license (<a href='https://www.nlm.nih.gov/databases/umls.html'>how to</a>) and API key (<a "
					 "href='https://www.nlm.nih.gov/research/umls/user_education/quick_tours/UTS-API/UTS_REST_API_Authentication.html'> "
					 "how to</a>) to use it. </p>"
					 "<p>Do you want to use this function?</p>"))
		yes_or_no = OptionButtons(options=['yes', 'no'], description='Choose an option: ', tooltips=['yes: use UMLS', 'no: not use UMLS'])
		clear_output(wait=True)
		yes_or_no.setOpitionalNextSteps([None, None])
		pass

	def chooseUMLSSource(self):
		display(HTML("<h4>Use UMLS heuristics:</h4>"
					 "<p>Use UMLS resources to expand your keywords through finding synonyms, hypernyms or hyponyms. </p>"
					 "<p>You will need UMLS license (<a href='https://www.nlm.nih.gov/databases/umls.html'>how to</a>) and API key (<a href='https://www.nlm.nih.gov/research/umls/user_education/quick_tours/UTS-API/UTS_REST_API_Authentication.html'>"
					 "how to</a>) to use it. </p>"
					 "<p>Do you want to use this function?</p>"))

	def initWordEmbedding(self, word2vec_file):
		if path.isfile(word2vec_file):
			if word2vec_file.endswith('.bin'):
				self.glove_model = KeyedVectors.load_word2vec_format(word2vec_file, binary=True)
			else:
				self.glove_model = KeyedVectors.load_word2vec_format(word2vec_file, binary=False)
				print('convert txt model to binary model...')
				self.glove_model.save_word2vec_format(word2vec_file + '.bin', binary=True)
		pass

	def initUMLS(self, username, password):
		pass

	def takeUserInput(self):
		pass

	def previous_word(self):
		pass

	def next_word(self):
		pass

	def reviewWords(self):
		pass

	def finish(self):
		self.data = self.words
		self.complete()
		pass

	def addWord(self, word):
		if word not in self.words_set:
			self.words_set[word] = None
			self.words.append(word)
		pass
