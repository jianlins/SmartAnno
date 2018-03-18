from os import path

import pandas as pd
from IPython.core.display import display
from ipywidgets import widgets

from gui.PreviousNextWidgets import PreviousNext
from gui.Workflow import Step


class ReadFiles(PreviousNext):
    """Display a progress bar to show files (set up by DirChooser) importing process"""

    def __init__(self, name=str(Step.global_id + 1), show_previous=True, show_next=True):
        super().__init__(name, show_previous, show_next)
        self.next_button.disabled = True
        self.resetParameters()
        pass

    def resetParameters(self):
        self.data = pd.DataFrame(columns=['doc_name', 'text'])
        pass

    def start(self):
        if self.previous_step.data is None:
            self.previous_step.start()
        parent_dir, files = self.previous_step.data
        label = widgets.HTML(description="<h4>Import files from: </h4><p>" + parent_dir + "</p>")
        progressbar = widgets.IntProgress(min=0, max=len(files), value=0, layout=widgets.Layout(width='50%'))
        rows = [label, progressbar] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        display(vbox)
        for i in range(0, len(files)):
            file = files[i]
            progressbar.value = i
            with open(parent_dir + '/' + file) as f:
                base_name = path.basename(file)
                text = f.read()
                self.data = self.data.append(pd.DataFrame([[base_name, text]], columns=['doc_name', 'text']))
        progressbar.value = progressbar.max
        self.next_button.disabled = False
        self.data.set_index('doc_name', inplace=True)
        print("Totally " + str(len(files)) + " files have been imported into dataframe.")

        return self.data
