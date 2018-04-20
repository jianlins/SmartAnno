from IPython.core.display import display

from SmartAnno.db.ORMs import Document, Task
from SmartAnno.gui.PreviousNextWidgets import PreviousNextWithOptions


class DataSetChooser(PreviousNextWithOptions):

    def start(self):
        self.updateBox()
        display(self.box)
        pass

    def updateBox(self):
        dao = self.workflow.dao
        options = []
        with dao.create_session() as session:
            results = session.query(Document.DATASET_ID).distinct()
            for res in results:
                options.append(res.DATASET_ID)
            value = session.query(Task.DATASET_ID).filter(Task.TASK_NAME == self.workflow.task_name).first()
            if value is not None:
                value = value[0]
        self.toggle.options = options
        self.toggle.value = value

        # display(self.box)
        pass

    def complete(self):
        self.workflow.dataset_id = self.toggle.value
        with self.workflow.dao.create_session() as session:
            task = session.query(Task).filter(Task.TASK_NAME == self.workflow.task_name).first()
            task.DATASET_ID = self.workflow.dataset_id
        super().complete()
        pass
