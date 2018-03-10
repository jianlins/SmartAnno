import time
from IPython.core.display import display, clear_output
import ipywidgets as widgets

from gui.Workflow import Step, SubStep


class TimerProgressBar(object):
	"""display a timer progress bar"""

	def __init__(self, wait_sec):
		num_half_sec = int(wait_sec * 2)
		progressbar = widgets.IntProgress(min=0, max=num_half_sec, value=0)
		display(progressbar)
		for i in range(0, num_half_sec):
			progressbar.value = i
			time.sleep(0.5)
		progressbar.value = num_half_sec
		pass


class PreviousNext(Step):
	def __init__(self, show_previous=True, show_next=True):
		super().__init__()
		self.show_previous = show_previous
		self.show_next = show_next
		self.box = self.createBox()
		pass

	def start(self):
		clear_output()
		display(self.box)
		pass

	def createBox(self):
		rows = self.addSeparator() + [self.addPreviousNext(self.show_previous, self.show_next)]
		vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
		return vbox

	def addSeparator(self, top='5px', bottom='1px', height='10px', width='98%', left='1%'):
		top_whitespace = widgets.Label(value='', layout=widgets.Layout(height=top))
		separator = widgets.IntProgress(min=0, max=1, value=1, layout=widgets.Layout(left=left, width=width, height=height))
		separator.style.bar_color = 'GAINSBORO'
		bottom_whitespace = widgets.Label(value='', layout=widgets.Layout(height=bottom))
		return [top_whitespace, separator, bottom_whitespace]

	def addPreviousNext(self, show_previous, show_next):
		def goBack(b):
			self.goBack()
			pass

		def goNext(b):
			self.complete()
			pass

		my_buttons = []
		if show_previous:
			previous_button = widgets.Button(description='Previous', layout=widgets.Layout(width='90px'))
			previous_button.style.button_color = 'SILVER'
			previous_button.on_click(goBack)
			my_buttons.append(previous_button)

		if show_next:
			next_button = widgets.Button(description='Next', layout=widgets.Layout(width='90px', left='100px'))
			next_button.style.button_color = 'SANDYBROWN'
			next_button.on_click(goNext)
			my_buttons.append(next_button)
		return widgets.HBox(my_buttons, layout=widgets.Layout(left='10%', width='80%'))


class PreviousNextWithOptions(PreviousNext):
	"""display toggle buttons, link each option with a next step function"""

	def __init__(self, options=[], value=None, description='', tooltips=[], button_style='', show_previous=True, show_next=True):
		self.toggle = widgets.ToggleButtons(
			options=options,
			description=description,
			disabled=False,
			value=value,
			button_style=button_style,  # 'success', 'info', 'warning', 'danger' or ''
			tooltips=tooltips,
			layout=widgets.Layout(width='70%')
			#     icons=['check'] * 3
		)
		self.toggle.observe(self.on_click, 'value')
		super().__init__(show_previous, show_next)
		# pad the descriptions list if it is shorter than options list
		self.resetParameters()
		pass

	def on_click(self, change):
		self.data = change['new']
		pass

	def createBox(self):
		rows = [self.toggle] + self.addSeparator(top='10px') + [self.addPreviousNext(self.show_previous, self.show_next)]
		vbox = widgets.VBox(rows)
		vbox.layout.flex_grown = 'column'
		return vbox


class PreviousNextTextArea(PreviousNext):
	"""display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""

	def __init__(self, description='Type your words/phrases below', value='', placeholder='each phrase/word per line', width='500px', height='300px',
				 show_previous=True,
				 show_next=True):
		self.data = value.split("\n")
		self.text_area = widgets.Textarea(
			value=value,
			placeholder='Type your word',
			description='String:',
			disabled=False,
			layout=widgets.Layout(width=width, height=height))
		super().__init__(show_previous, show_next)
		self.resetParameters()
		pass

	def createBox(self):
		rows = [self.text_area] + self.addSeparator(top='10px') + [self.addPreviousNext(self.show_previous, self.show_next)]
		vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
		return vbox

	def resetParameters(self):
		super().resetParameters()
		self.text_area.value = ''
		pass

	def complete(self):
		self.data = [item.strip() for item in self.text_area.value.split("\n")]
		super().complete()
		pass


class PreviousNextLabel(PreviousNext):
	"""display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""

	def __init__(self, description='Type your words/phrases below', show_previous=True,
				 show_next=True):
		self.label = widgets.Label(
			value=description)
		super().__init__(show_previous, show_next)
		self.resetParameters()
		pass

	def createBox(self):
		rows = [self.label] + self.addSeparator(top='10px') + [self.addPreviousNext(self.show_previous, self.show_next)]
		vbox = widgets.VBox(rows)
		vbox.layout.flex_grown = 'column'
		return vbox


class PreviousNextHTML(PreviousNext):
	"""display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""

	def __init__(self, description='<p>Introduction:</p>', show_previous=True,
				 show_next=True):
		self.html = widgets.HTML(
			value=description)
		super().__init__(show_previous, show_next)
		self.resetParameters()
		pass

	def createBox(self):
		rows = [self.html] + self.addSeparator(top='10px') + [self.addPreviousNext(self.show_previous, self.show_next)]
		vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
		return vbox
