from IPython.core.display import display

from db.ORMs import Document
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
        self.toggle.options = options
        # display(self.box)
        pass

    def complete(self):
        self.workflow.dataset_id = self.toggle.value
        super().complete()
        pass
