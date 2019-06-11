import os
import time
import ipywidgets as widgets
from ipywidgets import Layout, Box, HTML
from IPython.display import clear_output, display

from SmartAnno.gui.Workflow import Step


class FileChooser(Step):
    """Display a simple GUI to let users choose from which zip file to import the text documents"""

    def __init__(self, height=150, intro_wait=3.5):
        super().__init__()
        self.height = height
        self.intro_wait = intro_wait
        self.resetParameters()

    def resetParameters(self):
        super().__init__()
        self.path = os.getcwd()
        self.filter = ''
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
        display(HTML('<p><b>Welcome to SmartAnno!<br/>First let\'s import txt data from a zip file. </p>'))
        num_half_sec = int(self.intro_wait * 2)
        progressbar = widgets.IntProgress(min=0, max=num_half_sec, value=0)
        display(progressbar)
        for i in range(0, num_half_sec):
            progressbar.value = i
            time.sleep(0.5)
        progressbar.value = num_half_sec
        clear_output()
        box = widgets.VBox()
        self._update(box)
        display(box)
        return box

    def _update(self, box):

        def on_click(b):
            if b.description == '..':
                self.path = os.path.split(self.path)[0]
            else:
                self.path = self.path + "/" + b.description
            self._update_files()
            # print(self.files)
            # self.files.sort()
            # print(self.files)
            self._update(box)

        def on_confirm(b):
            clear_output(wait=False)
            if self.filter == '':
                file_type = 'all the '
            else:
                file_type = "'" + self.filter + "'"
            display(widgets.HTML("Start to import <b>" + file_type + "</b> files from: <br/>" + self.path))
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
            # button.on_click(on_click)
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
        file_filter.observe(update_filter, type='change')
        box.children = tuple([widgets.HTML("<h4>Import files from: </h4>")] +
                             [widgets.HTML("<p><b>Current directory: </b>%s</p>" % (self.path,))] + [carousel] + [
                                 file_filter] + [confirm])
