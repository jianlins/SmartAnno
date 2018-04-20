import traitlets
import ipywidgets as widgets

from SmartAnno.gui.Workflow import Step


def bind(widget, trait_name):
    """adopted from
    https://gist.github.com/aplavin/19f3607240c4c0a63cb1d223609ddc3b#file-mywidgets-py-L69"""
    def wrapper(func):
        if isinstance(widget, widgets.Widget):
            widget.observe(func, trait_name)
        else:
            for w in widget:
                w.observe(func, trait_name)
        func()

    return wrapper


class ToggleButtonsMulti(widgets.Box):
    """adopted from
    https://gist.github.com/aplavin/19f3607240c4c0a63cb1d223609ddc3b#file-mywidgets-py-L69"""

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

    def on_click(self, change):
        self.data = change['new']
        pass

    def createBox(self):
        rows = [self.toggle] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox