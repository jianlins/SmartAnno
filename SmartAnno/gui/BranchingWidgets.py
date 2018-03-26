from threading import Thread
from time import sleep

import ipywidgets as widgets
from IPython.core.display import display, clear_output

from conf.ConfigReader import ConfigReader
from gui.MyWidgets import ClickResponsiveToggleButtons
from gui.Workflow import Step, Workflow
from utils.GloveModel import GloveModel

"""
This file contains branching widgets
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

    def navigate(self, b):
        # print(b)
        b.linked_step.start()
        pass

    def addConditions(self):
        condition_steps = self.branch_steps
        for i in range(0, len(condition_steps)):
            if condition_steps[i] is not None and isinstance(condition_steps[i], Step):
                self.branch_buttons[i].linked_step = condition_steps[i]
                self.branch_buttons[i].on_click(self.navigate)
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
                self.complete()
            else:
                self.goBack()
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
            button_style='info',  # 'success', 'info', 'warning', 'danger' or ''
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
        print(self.workflow.data)
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
        else:
            previous_step = self.previous_step
        id = len(self.loop_workflow)
        self.loop_workflow.steps.append(newRepeatStep)
        self.loop_workflow.name_dict[newRepeatStep.name] = id
        self.loop_workflow.step_names.append(newRepeatStep.name)
        # print('attache new step' + newRepeatStep.name + "_" + str(id))
        newRepeatStep.setWorkflow(self.loop_workflow)
        if previous_step is not None and isinstance(previous_step, RepeatStep):
            previous_step.setNextRepeat(newRepeatStep)
            newRepeatStep.setPreviousRepeat(previous_step)
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


class IntroStep(BranchingStep):
    def __init__(self, description='', name=None):
        self.glove_path = ConfigReader.getValue('glove/path')
        self.glove_vocab = ConfigReader.getValue('glove/vocab')
        self.glove_vector = ConfigReader.getValue('glove/vector')
        if self.glove_vocab is None:
            self.glove_vocab = 1900000

        if self.glove_vector is None:
            self.glove_vector = 300
        self.html = widgets.HTML(value=description)
        super().__init__(name)
        pass

    def start(self):
        self.branch_buttons = [widgets.Button(description=d, layout=widgets.Layout(width='150px', left='100px')) for d
                               in
                               ['StartOver', 'ContinueReviewing']]
        self.branch_buttons[0].restore = False
        self.branch_buttons[1].restore = True
        clear_output()
        self.box = self.createBox()
        display(self.box)
        pass

    def navigate(self, button):
        if hasattr(self, "glove_path_input"):
            self.saveGloveConfig()
        self.backgroundWork()
        if button.restore:
            previous_status = self.workflow.restoreStatus()
            self.workflow.steps[1].start()
        else:
            self.workflow.steps[1].start()
        pass

    def saveGloveConfig(self):
        self.glove_path = self.glove_path_input.value
        self.glove_vocab = self.glove_vocab_input.value
        self.glove_vector = self.glove_vector_input.value
        self.workflow.glove_path = self.glove_path
        ConfigReader.setValue("glove/vocab", int(self.glove_vocab))
        ConfigReader.setValue("glove/vector", int(self.glove_vector))
        ConfigReader.setValue("glove/path", self.glove_path)
        ConfigReader.saveConfig()
        pass

    def createBox(self):
        rows = self.addSeparator()
        rows += [self.html]
        self.requestWELocation(rows)
        rows += self.addSeparator() + self.addConditions()
        # print('\n'.join([str(row) for row in rows]))
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def addConditions(self):
        for button in self.branch_buttons:
            button.on_click(self.navigate)
        return [widgets.HBox(self.branch_buttons, layout=widgets.Layout(left='10%', width='80%'))]

    def backgroundWork(self):
        thread_gm = Thread(target=self.prepareGloveModel)
        thread_gm.start()
        pass

    def prepareGloveModel(self):
        GloveModel(word2vec_file=self.glove_path, vocab=self.glove_vocab, vect=self.glove_vector)
        pass

    def requestWELocation(self, rows):
        if self.glove_path is None or self.glove_path.strip() == '':
            rows += self.addSeparator()
            rows.append(
                widgets.HTML(value='<h4>Set up your Glove model</h4><p>In order to use word embedding, you need '
                                   'to tell where the glove model locates:</p>'))
            self.glove_path_input = widgets.Text(
                value='models/saved/glove/glove.42B.300d.bin',
                placeholder='copy and paste your glove model file location here',
                description='',
                disabled=False,
                layout=widgets.Layout(width='70%')
            )

            self.glove_vocab_input = widgets.Text(value=str(self.glove_vocab),
                                                  placeholder='',
                                                  description='', disabled=False)
            self.glove_vector_input = widgets.Text(value=str(self.glove_vector),
                                                   placeholder='the vector size of the glove model',
                                                   description='', disabled=False)
            rows.append(self.glove_path_input)
            rows.append(widgets.HTML(value='The vocabulary size of the glove model:'))
            rows.append(self.glove_vocab_input)
            rows.append(widgets.HTML(value='The vector size of the glove model:'))
            rows.append(self.glove_vector_input)
            rows += self.addSeparator()
        pass
