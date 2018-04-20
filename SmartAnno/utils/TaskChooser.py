from IPython.core.display import clear_output, display
from ipywidgets import widgets

from SmartAnno.db.ORMs import Task
from SmartAnno.gui.PreviousNextWidgets import PreviousNextText


class TaskChooser(PreviousNextText):

    def __init__(self, description='<h4>Choose a task:</h4>', value='', placeholder='enter a name',
                 width='500px', name='task_chooser'):
        self.task_list = None
        super().__init__(description, value, placeholder, width, name)
        pass

    def start(self):
        self.readDB()
        display(self.box)
        pass

    def readDB(self):
        task_names = []
        task_name_id = dict()
        with self.workflow.dao.create_session() as session:
            records = session.query(Task)
            for record in records:
                task_names.append(record.TASK_NAME)
                task_name_id[record.TASK_NAME] = record.ID
        self.task_list = widgets.ToggleButtons(
            options=task_names,
            description='',
            disabled=False,
            value=None if len(task_names) == 0 else task_names[0],
            button_style='',  # 'success', 'info', 'warning', 'danger' or ''
            layout=widgets.Layout(width='70%')
            #     icons=['check'] * 3
        )
        self.updateBox()
        pass

    def updateBox(self):
        new_task_title = widgets.HTML(value='If you want to start a new task, type the name below:')
        rows = [self.title, self.task_list, new_task_title, self.text] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        self.box = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        pass

    def complete(self):
        value = self.text.value.strip()
        if len(value) == 0:
            value = self.task_list.value
        if value is None or value == '':
            print('You need either choose a task or input a new task name above')
            return
        self.data = value
        self.workflow.task_name = value
        if len(self.text.value.strip()) > 0:
            with self.workflow.dao.create_session() as session:
                session.add(Task(TASK_NAME=value))
        if self.workflow.to_continue:
            self.workflow.getStepByName('dataset_chooser').start()
            self.workflow.getStepByName('dataset_chooser').complete()
            self.workflow.getStepByName('types').complete()
            self.workflow.getStepByName('types').complete()
            self.workflow.getStepByName('keywords').next_step = None
            self.workflow.getStepByName('keywords').complete()
            self.workflow.getStepByName('rb_review_init').start()
            self.workflow.getStepByName('rb_review_init').complete()
        else:
            super().complete()
        pass
