import abc


from IPython.core.display import clear_output

from ipywidgets import widgets

from conf.ConfigReader import ConfigReader
from utils.NoteBookLogger import logMsg


class Step(object):
    """a step in a workflow"""
    global_id = -1

    def __init__(self, name=None):
        self.next_step = None
        self.previous_step = None
        Step.global_id += 1
        if name is not None and name != '':
            self.name = name + "_" + str(Step.global_id)
        else:
            self.name = str(type(self).__name__) + "_" + str(Step.global_id)
        self.data = None
        self.workflow = None
        self.pos_id = -1
        pass

    def setPreviousStep(self, previous_step):
        self.previous_step = previous_step
        pass

    def setWorkflow(self, workflow):
        if workflow is None:
            print('You cannot set a None workflow')
            return
        self.workflow = workflow
        pass

    def setNextStep(self, next_step):
        self.next_step = next_step
        pass

    @abc.abstractmethod
    def start(self):
        pass

    def backStart(self):
        self.start()
        pass

    def resetParameters(self):
        self.data = None
        pass

    def goBack(self):
        clear_output(True)
        if self.previous_step is not None:
            if isinstance(self.previous_step, Step):
                self.previous_step.resetParameters()
                self.workflow.updateStatus(self.previous_step.pos_id)
                self.previous_step.backStart()
            else:
                raise TypeError(
                    'Type error for ' + self.name + '\'s next_step. Only Step can be the next_step, where its next_step is ' + str(
                        type(self.next_step)))
        else:
            print("previous step hasn't been set.")
        pass

    def complete(self):
        clear_output(True)
        if self.next_step is not None:
            logMsg((self, 'workflow complete'))
            if isinstance(self.next_step, Step):
                if self.workflow is not None:
                    self.workflow.updateStatus(self.next_step.pos_id)
                self.next_step.start()
            else:
                raise TypeError(
                    'Type error for ' + self.name + '\'s next_step. Only Step can be the next_step, where its next_step is ' + str(
                        type(self.next_step)))
        else:
            print("next step hasn't been set.")
        pass

    def addSeparator(self, top='5px', bottom='1px', height='10px', width='98%', left='1%'):
        top_whitespace = widgets.Label(value='', layout=widgets.Layout(height=top))
        separator = widgets.IntProgress(min=0, max=1, value=1,
                                        layout=widgets.Layout(left=left, width=width, height=height))
        separator.style.bar_color = 'GAINSBORO'
        bottom_whitespace = widgets.Label(value='', layout=widgets.Layout(height=bottom))
        return [top_whitespace, separator, bottom_whitespace]

    def __repr__(self):
        return "<" + str(type(self).__name__) + "\tname:" + self.name + ">"


class Workflow(object):
    """a workflow consist a list of steps that are linked to each other. So that once one step is finished,
    it can trigger the next step to start."""
    global_id = 0

    def __init__(self, steps=[], name='workflow_' + str(global_id), config_file='conf/smartanno_conf2.json'):
        Workflow.global_id += 1
        self.name = name
        self.steps = []
        self.step_names = [None] * len(steps)
        self.name_dict = dict()
        self.status = 0
        self.config_file = config_file
        for step in steps:
            self.append(step)
        pass

    def start(self, restore=False):
        if restore:
            self.status = self.restoreStatus()
        else:
            self.status = 0
        if len(self.steps) > self.status:
            self.steps[self.status].start()

    def __len__(self):
        return len(self.steps)

    def append(self, new_step):
        # if not isinstance(new_step, type(Step)):
        #     raise TypeError(
        #         'Type error for ' + new_step + 'th steps. Only Step can be the next_step, where its next_step is '
        #         + str(type(new_step)))
        previous_step = None
        if len(self.steps) > 0:
            previous_step = self.steps[-1]
        id = len(self.steps)
        new_step.pos_id = id
        new_step.setWorkflow(self)
        self.steps.append(new_step)

        self.name_dict[new_step.name] = id
        if previous_step is not None:
            logMsg((self, 'attache new step ' + new_step.name + ' ' + str(id)))
            new_step.setPreviousStep(previous_step)
            previous_step.setNextStep(new_step)
            pass

    def getStepById(self, step_id):
        return self.steps[step_id]

    def getStepByName(self, step_name):
        if step_name in self.name_dict and self.name_dict[step_name] < len(self.steps):
            return self.steps[self.name_dict[step_name]]
        else:
            return None

    def getDataById(self, step_id):
        step = self.getStepById(step_id)
        if step is not None:
            return step.data
        else:
            return None

    def getDataByName(self, step_name):
        step = self.getStepByName(step_name)
        if step is not None:
            return step.data
        else:
            return None

    def updateStatus(self, status=None):
        if status is not None:
            self.status = status
        ConfigReader.saveStatus(self.status, status_key='status/' + self.name)

    def restoreStatus(self):
        status = ConfigReader.getValue('status/' + self.name)
        if status is None or status == '':
            status = 0
        return status

    def __repr__(self):
        return '<%s, %s>' % (type(self), self.name)
