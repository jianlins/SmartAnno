import abc

import ipywidgets as widgets
from IPython.core.display import display, clear_output

from SmartAnno.gui.MyWidgets import ClickResponsiveToggleButtons
from SmartAnno.gui.Workflow import Step, Workflow, logMsg

"""
This file contains branching widgets
"""


class BranchingStep(Step):
    def __init__(self, branch_names=[], branch_steps=[], name=None):
        super().__init__(name)
        self.branch_buttons = [widgets.Button(description=d, layout=widgets.Layout(width='90px', left='100px')) for d in
                               branch_names]
        self.branch_steps = branch_steps
        self.addConditions()
        self.box = self.createBox()
        pass

    def start(self):
        display(self.box)
        pass

    def createBox(self):
        rows = self.addSeparator() + self.addConditionsWidget()
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def navigate(self, b):
        # print(b)
        self.updateData(b)
        if hasattr(b, 'linked_step'):
            b.linked_step.start()
        else:
            self.complete()
        pass

    @abc.abstractmethod
    def updateData(self, *args):
        pass

    def addConditions(self):
        condition_steps = self.branch_steps
        for i in range(0, len(condition_steps)):
            if condition_steps[i] is not None and isinstance(condition_steps[i], Step):
                self.branch_buttons[i].linked_step = condition_steps[i]
                self.branch_buttons[i].navigate_direction = 1
                self.branch_buttons[i].on_click(self.navigate)
        pass

    def addConditionsWidget(self):
        return [widgets.HBox(self.branch_buttons, layout=widgets.Layout(left='10%', width='80%'))]


class RepeatStep(BranchingStep):
    """looping steps, has an option button to out (Complete)"""

    def __init__(self, branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None], name=None):
        super().__init__(branch_names, branch_steps, name)
        self.branch_buttons[0].navigate_direction = -1
        self.branch_buttons[1].navigate_direction = 1
        self.branch_buttons[2].navigate_direction = 1
        for i in range(0, len(self.branch_buttons)):
            branch_button = self.branch_buttons[i]
            branch_button.linked_step = branch_steps[i]
            branch_button.on_click(self.navigate)
        self.resetParameters()
        pass

    def createBox(self):
        rows = self.addSeparator() + self.addConditionsWidget()
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def setPreviousStep(self, previous_step):
        if isinstance(previous_step, Step):
            self.branch_buttons[0].linked_step = previous_step
        else:
            print(self, 'setPreviousStep', previous_step, 'is not an instance of Step')
        pass

    def setNextStep(self, next_step):
        if isinstance(next_step, Step):
            self.branch_buttons[1].linked_step = next_step
            self.next_step = next_step
        else:
            print(self, 'setNextStep', next_step, 'is not an instance of Step')
        pass

    def setCompleteStep(self, complete_step):
        if isinstance(complete_step, Step):
            if len(self.branch_buttons) > 2:
                self.branch_buttons[2].linked_step = complete_step
        else:
            print(self, 'setCompleteStep', complete_step, 'is not an instance of Step')
        pass

    def navigate(self, b):
        clear_output(True)
        self.updateData(b)
        logMsg((b, hasattr(b, "linked_step")))
        if hasattr(b, 'linked_step') and b.linked_step is not None:
            b.linked_step.start()
        else:
            if not hasattr(b, 'navigate_direction') or b.navigate_direction == 1:
                self.complete()
            else:
                self.goBack()
        pass


class RepeatHTMLToggleStep(RepeatStep):
    def __init__(self, value=None, description='', options=[], tooltips=[],
                 branch_names=['Previous', 'Next', 'Complete'], branch_steps=[None, None, None], js='', end_js='',
                 name=None, button_style='info', reviewed=False):
        self.display_description = widgets.HTML(value=description)
        self.reviewed = reviewed
        self.toggle = ClickResponsiveToggleButtons(
            options=options,
            description='',
            disabled=False,
            value=value,
            button_style=button_style,  # 'success', 'info', 'warning', 'danger' or ''
            tooltips=tooltips,
            layout=widgets.Layout(width='70%')
            #     icons=['check'] * 3
        )
        self.js = js
        self.end_js = end_js
        self.toggle.on_click(self.on_click_answer)
        super().__init__(branch_names, branch_steps, name)
        pass

    def start(self):
        if len(self.js) > 0:
            display(widgets.HTML(self.js))
        display(self.box)
        pass

    def on_click_answer(self, toggle):
        if len(self.end_js) > 0:
            display(widgets.HTML(self.end_js))
        self.reviewed = True
        self.navigate(self.branch_buttons[1])
        pass

    def updateData(self, *args):
        self.data = self.toggle.value
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
        pass

    def createBox(self):
        rows = [self.display_description] + \
               [self.toggle] + self.addSeparator(top='10px') + self.addConditionsWidget()
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox


class LoopRepeatSteps(Step):
    """Wrapping multiple RepeatStep(s) in a workflow to build a mega Step"""

    def __init__(self, repeat_steps=[], name=None):
        super().__init__(name)
        self.loop_workflow = Workflow(name=name + "_loop")
        self.loop_workflow.data = dict()
        self.data = self.loop_workflow.data
        for step in repeat_steps:
            step.pos_id = len(self.loop_workflow)
            step.setWorkflow(self.loop_workflow)
            self.appendRepeatStep(step)
        pass

    def appendRepeatStep(self, newRepeatStep):
        if len(self.loop_workflow) > 0:
            previous_step = self.loop_workflow.steps[-1]
            previous_step.setNextStep(newRepeatStep)
        else:
            previous_step = self.previous_step
        #  first step in the loop, set previous step to the previous step outside the loop
        if len(self.loop_workflow.steps) == 0:
            newRepeatStep.setPreviousStep(previous_step)
        #  if the loop master step has next step, assign the complete buttons of repeat steps linked to that step.
        if self.next_step is not None:
            newRepeatStep.setCompleteStep(self.next_step)

        self.loop_workflow.append(newRepeatStep)

        pass

    def setNextStep(self, next_step):
        # need to update every embedded repeat steps
        for repeat_step in self.loop_workflow.steps:
            repeat_step.setCompleteStep(next_step)
        super().setNextStep(next_step)
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
