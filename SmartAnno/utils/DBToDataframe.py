from SmartAnno.db.ORMs import Annotation, Document
from SmartAnno.gui.PreviousNextWidgets import PreviousNext
from sqlalchemy import func, join, select
import pandas as pd


class DBToDataframe(PreviousNext):
    """Read previous saved annotations into dataframe to continue reviewing+training"""

    def __init__(self, name=None):
        super().__init__(name, show_previous=False, show_next=False)
        self.dao = None
        pass

    def start(self):
        self.dao = self.workflow.dao
        session = self.dao.create_session()
        last_run_id = session.query(func.max('run_id')).filter_by(Annotation.TASK_ID == self.workflow.task_id).get(1)
        s = join(Annotation, Document).select().where(Annotation.RUN_ID == last_run_id)
        self.data = pd.read_sql(s, self.dao._engine)
        if len(self.data) == 0:
            self.data = self.predict()
        self.workflow.data = self.data
        self.next_step.start()
        pass

    def predict(self):
        s = select([Document])
        
        return None
