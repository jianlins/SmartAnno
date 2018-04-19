import ipywidgets as widgets
from IPython.core.display import display
from traitlets import traitlets


class ClickResponsiveToggleButtons(widgets.ToggleButtons):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._click_handlers = widgets.CallbackDispatcher()
        self.on_msg(self._handle_button_msg)
        pass

    def on_click(self, callback, remove=False):
        """Register a callback to execute when the button is clicked.

        The callback will be called with one argument, the clicked button
        widget instance.

        Parameters
        ----------
        remove: bool (optional)
            Set to true to remove the callback from the list of callbacks.
        """
        self._click_handlers.register_callback(callback, remove=remove)

    def _handle_button_msg(self, _, content, buffers):
        """Handle a msg from the front-end.

        Parameters
        ----------
        content: dict
            Content of the msg.
        """
        if content.get('event', '') == 'click':
            self._click_handlers(self)


def monitor(wts, trait_name):
    def wrapper(func):
        if isinstance(wts, widgets.Widget):
            wts.observe(func, trait_name)
        else:
            for w in wts:
                w.observe(func, trait_name)
        func()

    return wrapper


class ToggleButtonsMultiSelection(widgets.Box):
    description = traitlets.Unicode()
    value = traitlets.Tuple()
    options = traitlets.Union([traitlets.List(), traitlets.Dict()])

    def __init__(self, num_per_row=5, **kwargs):
        super().__init__(**kwargs)
        self._selection_obj = widgets.widget_selection._MultipleSelection()
        traitlets.link((self, 'options'), (self._selection_obj, 'options'))
        traitlets.link((self, 'value'), (self._selection_obj, 'value'))

        @monitor(self, 'options')
        def _(*_):
            self.buttons = [widgets.ToggleButton(description=label,
                                                 layout=widgets.Layout(margin='2', icon='check'))
                            for label in self._selection_obj._options_labels]
            self.children = self.buttons

            @monitor(self.buttons, 'value')
            def _(*_):
                for btn in self.buttons:
                    btn.button_style = 'info' if btn.value else ''
                self.value = tuple(value
                                   for btn, value in zip(self.buttons, self._selection_obj._options_values)
                                   if btn.value)

        self.add_class('btn-group')


class ToggleButtonsMultiSelectionInBox(widgets.Box):
    description = traitlets.Unicode()
    value = traitlets.Tuple()
    options = traitlets.Union([traitlets.List(), traitlets.Dict()])

    def __init__(self, num_per_row=5, **kwargs):
        super().__init__(**kwargs)
        self._selection_obj = widgets.widget_selection._MultipleSelection()
        traitlets.link((self, 'options'), (self._selection_obj, 'options'))
        traitlets.link((self, 'value'), (self._selection_obj, 'value'))
        self.num_per_row = num_per_row

        @monitor(self, 'options')
        def _(*_):
            self.buttons = [widgets.ToggleButton(description=label, tooltip=label,
                                                 layout=widgets.Layout(margin='2', icon='check', width='100%',
                                                                       min_width='160px'))
                            for label in self._selection_obj._options_labels]
            rows = []
            for i in range(0, len(self.buttons), self.num_per_row):
                if i < len(self.buttons) - num_per_row:
                    rows.append(widgets.HBox(self.buttons[i:i + self.num_per_row]))
                else:
                    rows.append(widgets.HBox(self.buttons[i:]))

            self.children = [widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))]

            @monitor(self.buttons, 'value')
            def _(*_):
                for btn in self.buttons:
                    btn.button_style = 'info' if btn.value or btn.description in self.value else ''
                self.value = tuple(value
                                   for btn, value in zip(self.buttons, self._selection_obj._options_values)
                                   if btn.value)

        self.add_class('btn-group')


display(ToggleButtonsMultiSelectionInBox())
