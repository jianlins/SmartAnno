import time
import ipywidgets as widgets
import traitlets
from IPython.core.display import display, clear_output

from gui.Workflow import Step, logConsole


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
    def __init__(self, name=str(Step.global_id + 1), show_previous=True, show_next=True):
        super().__init__(name)
        self.next_button = None
        self.previous_button = None
        self.show_previous = show_previous
        self.show_next = show_next
        self.box = self.createBox()

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
        separator = widgets.IntProgress(min=0, max=1, value=1,
                                        layout=widgets.Layout(left=left, width=width, height=height))
        separator.style.bar_color = 'GAINSBORO'
        bottom_whitespace = widgets.Label(value='', layout=widgets.Layout(height=bottom))
        return [top_whitespace, separator, bottom_whitespace]

    def addPreviousNext(self, show_previous=True, show_next=True):
        def goBack(b):
            self.goBack()
            pass

        def goNext(b):
            logConsole('next clicked')
            self.complete()
            pass

        if show_previous and self.previous_button is None:
            self.previous_button = widgets.Button(description='Previous', layout=widgets.Layout(width='90px'))
            self.previous_button.style.button_color = 'SILVER'
            self.previous_button.on_click(goBack)

        if show_next and self.next_button is None:
            self.next_button = widgets.Button(description='Next', layout=widgets.Layout(width='90px', left='100px'))
            self.next_button.style.button_color = 'SANDYBROWN'
            self.next_button.on_click(goNext)
        return widgets.HBox([self.previous_button, self.next_button], layout=widgets.Layout(left='10%', width='80%'))


class PreviousNextWithOptions(PreviousNext):
    """display toggle buttons, link each option with a next step function"""

    def __init__(self, options=[], value=None, description='', tooltips=[], button_style='',
                 name=None, show_previous=True, show_next=True):
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
        super().__init__(name, show_previous, show_next)
        # pad the descriptions list if it is shorter than options list
        self.resetParameters()
        pass

    def on_click(self, change):
        self.data = change['new']
        pass

    def createBox(self):
        rows = [self.toggle] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox


class PreviousNextTextArea(PreviousNext):
    """display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""

    def __init__(self, description='Type your words/phrases below', value='', placeholder='each phrase/word per line',
                 width='500px', height='300px', name=str(Step.global_id + 1),
                 show_previous=True,
                 show_next=True):
        self.data = value.split("\n")
        self.title = widgets.HTML(value=description)
        self.text_area = widgets.Textarea(
            value=value,
            placeholder=placeholder,
            description='',
            disabled=False,
            layout=widgets.Layout(width=width, height=height))
        super().__init__(name, show_previous, show_next)
        self.resetParameters()
        pass

    def createBox(self):
        rows = [self.title, self.text_area] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
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


class PreviousNextText(PreviousNext):
    """display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""

    def __init__(self, description='Name your task:', value='', placeholder='enter a name',
                 width='500px', name=str(Step.global_id + 1), workflow_attribute='task_name',
                 show_previous=True,
                 show_next=True):
        self.data = value.split("\n")
        self.workflow_attribute = workflow_attribute
        self.title = widgets.HTML(value=description)
        self.text = widgets.Text(
            value=value,
            placeholder=placeholder,
            description='',
            disabled=False,
            layout=widgets.Layout(width=width))
        self.text.observe(self.submit, 'value')
        self.text.continuous_update = False
        super().__init__(name, show_previous, show_next)
        self.resetParameters()
        pass

    def createBox(self):
        rows = [self.title, self.text] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def resetParameters(self):
        super().resetParameters()
        self.text.value = ''
        pass

    def submit(self, value):
        self.data = self.text.value.strip()
        setattr(self.workflow, self.workflow_attribute, self.data)
        self.complete()
        pass

    def complete(self):
        super().complete()
        pass


class PreviousNextLabel(PreviousNext):
    """display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""

    def __init__(self, description='Type your words/phrases below',
                 name=str(Step.global_id + 1),
                 show_previous=True,
                 show_next=True):
        self.label = widgets.Label(
            value=description)
        super().__init__(name, show_previous, show_next)
        self.resetParameters()
        pass

    def createBox(self):
        rows = [self.label] + self.addSeparator(top='10px') + [self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox


class PreviousNextHTML(PreviousNext):
    """display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""

    def __init__(self, description='<p>Introduction:</p>',
                 name=str(Step.global_id + 1),
                 show_previous=True,
                 show_next=True):
        self.html = widgets.HTML(
            value=description)
        super().__init__(name, show_previous, show_next)
        self.resetParameters()
        pass

    def createBox(self):
        rows = [self.html] + self.addSeparator(top='10px') + [self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox


class PreviousNextIntSlider(PreviousNext):
    def __init__(self, value=60, min=0, max=100, step=10, description='Choose the percentage below:',
                 name=str(Step.global_id + 1), show_previous=True, show_next=True):
        self.title = widgets.HTML(description)
        self.slider = widgets.IntSlider(
            value=value,
            min=min,
            max=max,
            step=step,
            description='',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d'
        )
        super().__init__(name, show_previous, show_next)
        self.resetParameters()
        pass

    def createBox(self):
        rows = [self.title, self.slider] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def complete(self):
        self.data = self.slider.value
        super().complete()
        pass


class PreviousNextMultiToggle(PreviousNext):
    def __init__(self, options=[], value=None, description='', tooltips=[], button_style='',
                 name=str(Step.global_id + 1), show_previous=True, show_next=True):
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
        super().__init__(name, show_previous, show_next)
        # pad the descriptions list if it is shorter than options list
        self.resetParameters()
        pass


class PreviousNextToggleButtonsMulti(PreviousNext):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selection_obj = widgets.widget_selection._MultipleSelection()
        traitlets.link((self, 'options'), (self._selection_obj, 'options'))
        traitlets.link((self, 'value'), (self._selection_obj, 'value'))

        @traitlets.observe(self, 'options')
        def _(*_):
            self.buttons = [widgets.ToggleButton(description=label,
                                                 layout=widgets.Layout(margin='0', width='auto'))
                            for label in self._selection_obj._options_labels]
            self.children = self.buttons

            @traitlets.observe(self.buttons, 'value')
            def _(*_):
                for btn in self.buttons:
                    btn.button_style = 'primary' if btn.value else ''
                self.value = tuple(value
                                   for btn, value in zip(self.buttons, self._selection_obj._options_values)
                                   if btn.value)

        self.add_class('btn-group')

    def reset(self):
        opts = self.options
        self.options = []
        self.options = opts
