from time import sleep

import pandas as pd
from IPython.core.display import clear_output, display
from sqlalchemy import select

from db.ORMs import Task, Typedef
from gui.PreviousNextWidgets import PreviousNextTextArea
from gui.Workflow import Step


class AnnotationTypeDef(PreviousNextTextArea):
    """display a input text field, with optional button: 'submit', 'cancel', and 'finish'"""

    def __init__(self, description='Type your words/phrases below', value='', placeholder='each phrase/word per line',
                 width='500px', height='300px', name=str(Step.global_id + 1)):
        super().__init__(description, value, placeholder, width, height, name)
        pass

    def start(self):
        clear_output()
        self.readDB()
        display(self.box)
        pass

    def readDB(self):
        self.workflow.task_id = None
        with self.workflow.dao.create_session() as session:
            task = session.query(Task).filter(Task.task_name == self.workflow.task_name).first()
            if task is None:
                session.add(Task(task_name=self.workflow.task_name))
                session.commit()
                task = session.query(Task).filter(Task.task_name == self.workflow.task_name).first()
                self.workflow.task_id = task.id
            else:
                self.workflow.task_id = task.id
        s = select([Typedef]).where(Typedef.task_id == self.workflow.task_id)
        df = pd.read_sql(s, self.workflow.dao._engine)
        self.data = df['type_name'].values.tolist()
        self.text_area.value = '\n'.join(self.data)
        pass

    def complete(self):
        self.data = [item.strip() for item in self.text_area.value.split("\n") if len(item.strip()) > 0]
        with self.workflow.dao.create_session() as session:
            session.query(Typedef).filter(Typedef.task_id == self.workflow.task_id).delete()
            session.add_all([Typedef(type_name=type_name, task_id=self.workflow.task_id) for type_name in self.data])
        super().complete()
        pass
