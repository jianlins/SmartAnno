import os

import ipywidgets as widgets
from IPython.display import clear_output, display
from ipywidgets import Layout, Box

from SmartAnno.gui.Workflow import Step


class DirChooser(Step):
    """Display a simple GUI to let users choose from which directory to import the text files"""

    def __init__(self, height=150, intro_wait=3.5, title='Import files from: ', name=str(Step.global_id + 1),
                 path=None):
        super().__init__(name)
        self.notice = ''
        self.box = None
        self.title = title
        self.height = height
        self.intro_wait = intro_wait
        self.path = path
        self.resetParameters()

    def resetParameters(self):
        if self.data is not None and isinstance(self.data, tuple) and len(self.data) > 0:
            self.data[1].clear()
        if self.path is None:
            self.path = os.getcwd()
        self.file = ''
        self.filter = 'txt'
        self._update_files()
        pass

    def _update_files(self):
        self.files = list()
        self.dirs = list()
        if os.path.isdir(self.path):
            for f in os.listdir(self.path):
                ff = self.path + "/" + f
                if os.path.isdir(ff):
                    self.dirs.append(f)
                elif f.lower().endswith(self.filter.lower()):
                    self.files.append(f)
        self.dirs.sort()
        self.files.sort()

    def start(self):
        # display(HTML('<p><b>Welcome to SmartAnno!<br/>First let\'s import txt data from a directory. </p>'))
        # TimerProgressBar(self.intro_wait)
        clear_output()
        if not self.workflow.getStepByName('db_initiator').need_import:
            self.workflow.steps[self.pos_id + 3].setPreviousStep(self.workflow.steps[1])
            self.workflow.steps[self.pos_id + 3].start()
            return None
        self.box = widgets.VBox(layout=widgets.Layout(display='flex', flex_grown='column'))
        self._update(self.box)
        display(self.box)
        return self.box

    def _update(self, box):
        def on_click(b):
            if b.description == '..':
                self.path = os.path.split(self.path)[0]
            else:
                self.path = self.path + "/" + b.description
            for button in box.children[2].children:
                button.disabled = True
            self._update_files()
            self.file = ''
            # print(self.files)
            # self.files.sort()
            # print(self.files)

            self._update(box)

        def on_select(b):
            self.file = b.description
            self.notice = "<p><b>Current selected zip file: </b>%s</p>" % (self.file,)
            self._update(box)
            pass

        def on_confirm(b):
            clear_output()
            if self.filter == '':
                file_type = 'all the '
            else:
                file_type = "'" + self.filter + "'"
            display(widgets.HTML("Start to import <b>" + file_type + "</b> files from: <br/>" + self.path))
            if len(self.file) > 0:
                self.data = (self.file, self.files)
            else:
                self.data = (self.path, self.files)
            self.complete()
            pass

        def update_filter(fil):
            if len(fil['new']) > 0:
                if type(fil['new']) is dict:
                    self.filter = fil['new']['value']
                else:
                    self.filter = fil['new']
            else:
                if type(fil['old']) is dict:
                    self.filter = fil['old']['value']
                else:
                    self.filter = fil['old']
            self._update_files()
            self._update(box)
            pass

        buttons = []
        # if self.files:
        button = widgets.Button(description='..')
        button.style.button_color = 'lightgreen'
        button.on_click(on_click)
        buttons.append(button)
        for f in self.dirs:
            button = widgets.Button(description=f)
            button.style.button_color = 'lightgreen'
            button.on_click(on_click)
            buttons.append(button)
        for f in self.files:
            button = widgets.Button(description=f)
            if f.lower().endswith('zip'):
                button.on_click(on_select)
            buttons.append(button)

        box_layout = Layout(overflow_y='auto', display='block', height=str(self.height) + 'px', border='1px solid grey')
        carousel = Box(children=buttons, layout=box_layout)
        confirm = widgets.Button(description="Confirm")
        confirm.style.button_color = 'SANDYBROWN'
        confirm.on_click(on_confirm)
        file_filter = widgets.Text(
            value=self.filter,
            placeholder='file type filter to import',
            description='Only import type:',
            disabled=False
        )
        file_filter.continuous_update = False
        file_filter.observe(update_filter, type='change')
        self.notice = "<p><b>Current directory: </b>%s</p>" % (self.path,)
        if len(self.file) > 0:
            self.notice = "<p><b>Current selected zip file: </b>%s</p>" % (self.file,)
        box.children = tuple([widgets.HTML("<h4>" + self.title + "</h4>")] +
                             [widgets.HTML(self.notice)] + [carousel] + [
                                 file_filter] + [confirm])
