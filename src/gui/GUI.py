from gui.CustomWidgets import PreviousNextTextArea, PreviousNextLabel, PreviousNextHTML
from gui.DirChooser import DirChooser
from gui.FileIO import ReadFiles
# from gui.SetFilterKeyWords import SetFilterKeyWords
from gui.Workflow import Workflow


class GUI:
	"""Define and execute a workflow"""

	def __init__(self):
		self.data = None
		self.dir_chooser = None
		self.data = None
		self.ready = False
		self.workflow = None
		pass

	def start(self):
		self.workflow = Workflow([PreviousNextHTML('<p><b>Welcome to SmartAnno!<br/>First let\'s import txt data from a directory. </p>'
												   '<br/>',False),
								  DirChooser(), ReadFiles(),PreviousNextTextArea(description='Type your keywords filter below: ')])
		self.workflow.start()
		pass

	def getData(self):
		return self.workflow.data

	def getLastStepData(self):
		length = len(self.workflow.data)
		if length > 0:
			return self.workflow.data[length - 1]
		else:
			return None
