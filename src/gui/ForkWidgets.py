from _ast import List

import ipywidgets as widgets
from IPython.core.display import display, clear_output

from gui.ClickResponsiveToggleButtons import ClickResponsiveToggleButtons
from gui.Workflow import Step, Workflow

"""
This file contains 
"""


class BranchingStep(Step):
    def __init__(self, branch_names=[], branch_steps=[], name=None):
        super().__init__(name)
        self.branch_buttons = [widgets.Button(description=d, layout=widgets.Layout(width='90px', left='100px')) for d in
                               branch_names]
        self.branch_steps = branch_steps
        self.box = self.createBox()
        pass

    def start(self):
        clear_output()
        display(self.box)
        pass

    def createBox(self):
        rows = self.addSeparator() + self.addConditions()
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def addSeparator(self, top='5px', bottom='1px', height='10px', width='98%', left='1%'):
        top_whitespace = widgets.Label(value='', layout=widgets.Layout(height=top))
        separator = widgets.IntProgress(min=0, max=1, value=1,
                                        layout=widgets.Layout(left=left, width=width, height=height))
        separator.style.bar_color = 'GAINSBORO'
        bottom_whitespace = widgets.Label(value='', layout=widgets.Layout(height=bottom))
        return [top_whitespace, separator, bottom_whitespace]

    def addConditions(self):
        def navigate(b):
            # print(b)
            b.linked_step.start()
            pass

        condition_steps = self.branch_steps
        for i in range(0, len(condition_steps)):
            if condition_steps[i] is not None and isinstance(condition_steps[i], Step):
                self.branch_buttons[i].linked_step = condition_steps[i]
                self.branch_buttons[i].on_click(navigate)
        return [widgets.HBox(self.branch_buttons, layout=widgets.Layout(left='10%', width='80%'))]


class RepeatStep(BranchingStep):
    """looping steps, has an option button to out (Complete)"""

    def __init__(self, branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None], name=None):
        super().__init__(branch_names, branch_steps, name)
        self.branch_buttons[0].navigate_direction = -1
        self.branch_buttons[1].navigate_direction = 1
        for branch_button in self.branch_buttons:
            branch_button.on_click(self.navigate)
        self.resetParameters()
        pass

    def createBox(self):
        rows = self.addSeparator() + self.addConditions()
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def setPreviousRepeat(self, previous_repeat_step):
        if isinstance(previous_repeat_step, Step):
            self.branch_buttons[0].linked_step = previous_repeat_step
        else:
            print(previous_repeat_step, 'is not an instance of Step')
        pass

    def setNextRepeat(self, next_repeat_step):
        if isinstance(next_repeat_step, Step):
            self.branch_buttons[1].linked_step = next_repeat_step
        else:
            print(next_repeat_step, 'is not an instance of Step')
        pass

    def navigate(self, b):
        if hasattr(b, 'linked_step') and b.linked_step is not None:
            b.linked_step.start()
        else:
            if b.navigate_direction == 1:
                if self.next_step is not None:
                    self.next_step.start()
                else:
                    print(b, "the 'linked_step' is not set, neither is the 'next_step'.")
            else:
                if self.previous_step is not None:
                    self.previous_step.start()
                else:
                    print(b, "the 'linked_step' is not set, neither is the 'previous_step'.")
        pass


class RepeatHTMLToggleStep(RepeatStep):
    def __init__(self, value=None, description='', options=[], tooltips=[],
                 branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None],
                 name=None):
        self.display_description = widgets.HTML(value=description)
        self.toggle = ClickResponsiveToggleButtons(
            options=options,
            description='',
            disabled=False,
            value=value,
            button_style='',  # 'success', 'info', 'warning', 'danger' or ''
            tooltips=tooltips,
            layout=widgets.Layout(width='70%')
            #     icons=['check'] * 3
        )
        self.toggle.on_click(self.on_click_answer)
        super().__init__(branch_names, branch_steps, name)
        pass

    def on_click_answer(self, toggle):
        self.data = toggle.value
        # when choose a option, automatically move to next case
        if self.workflow is not None:
            if self.workflow.data is not None:
                if type(self.workflow.data) == dict:
                    if 'reviewed' not in self.workflow.data:
                        self.workflow.data['reviewed'] = []
                    if self.pos_id >= len(self.workflow.data['reviewed']):
                        self.workflow.data['reviewed'].append(self.data)
                    else:
                        self.workflow.data['reviewed'][self.pos_id] = self.data
                else:
                    print('the workflow data within repeated steps loop is not a ditionary')
            else:
                self.workflow.data = {'reviewed': [self.data]}
        else:
            print('the workflow is not set for the repeated step')
        self.navigate(self.branch_buttons[1])
        pass

    def createBox(self):
        rows = [self.display_description] + self.addSeparator(top='5px') + \
               [self.toggle] + self.addSeparator(top='10px') + self.addConditions()
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox


class LoopRepeatSteps(Step):
    """Wrapping multiple RepeatStep(s) in a workflow to build a mega Step"""

    def __init__(self, repeat_steps=[], name=None):
        super().__init__(name)
        self.data = dict()
        self.loop_workflow = Workflow()
        for step in repeat_steps:
            step.setWorkflow(self.workflow)
            self.appendRepeatStep(step)
        pass

    def appendRepeatStep(self, newRepeatStep):
        previous_step = None
        if len(self.loop_workflow.steps) > 0:
            previous_step = self.loop_workflow.steps[-1]
        id = len(self.loop_workflow.steps)
        self.loop_workflow.steps.append(newRepeatStep)
        self.loop_workflow.name_dict[newRepeatStep.name] = id
        self.loop_workflow.step_names.append(newRepeatStep.name)
        # print('attache new step' + newRepeatStep.name + "_" + str(id))
        newRepeatStep.setPreviousRepeat(previous_step)
        if previous_step is not None:
            previous_step.setNextRepeat(newRepeatStep)
        newRepeatStep.setPreviousStep(self.previous_step)
        newRepeatStep.setNextStep(self.next_step)

        pass

    def start(self):
        self.loop_workflow.start()
        pass


class LoopReviews(LoopRepeatSteps):
    """Wrapping multiple RepeatStep(s) in a workflow to build a mega Step"""

    def __init__(self, values=[], descriptions=[], options=[], tooltips=[], name=None):
        repeat_steps = []
        for i in range(0, len(descriptions)):
            repeat_steps.append(RepeatHTMLToggleStep(values[i], descriptions[i], options, tooltips))
        super().__init__(repeat_steps, name)
        pass
