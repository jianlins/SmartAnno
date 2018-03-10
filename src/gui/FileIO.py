import pandas as pd
from os import path

import time
from IPython.core.display import display, clear_output
from ipywidgets import widgets

from gui.Workflow import Step


class ReadFiles(Step):
	"""Display a progress bar to show files (set up by DirChooser) importing process"""

	def __init__(self):
		super().__init__()
		self.resetParameters()
		pass

	def resetParameters(self):
		self.data = pd.DataFrame(columns=['file_name', 'text'])
		pass

	def start(self):
		parent_dir, files = self.previous_step.data
		progressbar = widgets.IntProgress(min=0, max=len(files), value=0)
		display(progressbar)
		for i in range(0, len(files)):
			file = files[i]
			progressbar.value = i
			with open(parent_dir + '/' + file) as f:
				base_name = path.basename(file)
				text = f.read()
				self.data = self.data.append(pd.DataFrame([[base_name, text]], columns=['file_name', 'text']))
		progressbar.value = progressbar.max
		self.data.set_index('file_name', inplace=True)
		print("Totally " + str(len(files)) + " files have been imported into dataframe.")
		time.sleep(3)
		clear_output(wait=True)
		self.complete()
		return self.data
