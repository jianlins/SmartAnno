from IPython.core.display import display

from db.ORMs import Document, Task
from gui.PreviousNextWidgets import PreviousNextWithOptions


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
            value = session.query(Task.DATASET_ID).filter(Task.TASK_NAME == self.workflow.task_name).first()[0]
        self.toggle.options = options
        self.toggle.value = value

        # display(self.box)
        pass

    def complete(self):
        self.workflow.dataset_id = self.toggle.value
        super().complete()
        pass
