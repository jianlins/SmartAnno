from time import sleep

import pandas as pd
from IPython.core.display import clear_output, display
from ipywidgets import widgets
from sqlalchemy import select

from SmartAnno.db.ORMs import Task, Typedef
from SmartAnno.gui.PreviousNextWidgets import PreviousNextTextArea
from SmartAnno.gui.Workflow import Step


class AnnotationTypeDef(PreviousNextTextArea):
    """display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""
    neutral_type = 'Irrelevant'

    def __init__(self, description='Type your words/phrases below', value='', placeholder='each phrase/word per line',
                 width='500px', height='300px', name=str(Step.global_id + 1)):
        super().__init__(description, value, placeholder, width, height, name)
        self.addIrrelevant = None
        pass

    def start(self):
        self.readDB()
        self.box = self.updateBox()
        display(self.box)
        pass

    def updateBox(self):
        rows = [self.title, self.text_area]
        exist_types = set(item.strip() for item in self.text_area.value.split("\n") if
                          len(item.strip()) > 0)
        if self.workflow.dataset_id.endswith('_sents') and AnnotationTypeDef.neutral_type not in exist_types:
            print('added')
            desc = widgets.HTML(value='You choose sentences dataset, adding an additional type "Irrelevant"'
                                      ' is recommended. Because in most of cases, you will likely to sample a '
                                      'sentence that does not fall into the types that you defined. Do you want to add it? ')
            self.addIrrelevant = widgets.ToggleButtons(options=['Yes', 'No'])
            rows += self.addSeparator(top='10px')
            rows.append(desc)
            rows.append(self.addIrrelevant)
        rows += self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        return vbox

    def readDB(self):
        self.workflow.task_id = None
        with self.workflow.dao.create_session() as session:
            task = session.query(Task).filter(Task.TASK_NAME == self.workflow.task_name).first()
            if task is None:
                session.add(Task(task_name=self.workflow.task_name))
                session.commit()
                task = session.query(Task).filter(Task.TASK_NAME == self.workflow.task_name).first()
                self.workflow.task_id = task.ID
            else:
                self.workflow.task_id = task.ID
        s = select([Typedef]).where(Typedef.task_id == self.workflow.task_id)
        df = pd.read_sql(s, self.workflow.dao._engine)
        self.data = df['type_name'].values.tolist()
        self.text_area.value = '\n'.join(self.data)
        pass

    def complete(self):
        self.data = [item.strip() for item in self.text_area.value.split("\n") if len(item.strip()) > 0]
        if AnnotationTypeDef.neutral_type not in self.data and self.addIrrelevant is not None and self.addIrrelevant.value == 'Yes':
            self.data.append(AnnotationTypeDef.neutral_type)
        with self.workflow.dao.create_session() as session:
            session.query(Typedef).filter(Typedef.task_id == self.workflow.task_id).delete()
            session.add_all([Typedef(type_name=type_name, task_id=self.workflow.task_id) for type_name in self.data])
        self.workflow.types = self.data
        super().complete()
        pass
