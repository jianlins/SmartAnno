import os
from time import sleep

import sqlalchemy_dao
from IPython.core.display import clear_output, display
from ipywidgets import widgets
from sqlalchemy_dao import Dao
from sqlalchemy_dao import Model

from conf.ConfigReader import ConfigReader
from gui.PreviousNextWidgets import PreviousNext, PreviousNextText
from gui.Workflow import Step
from sqlalchemy import func

from db.ORMs import Task, Typedef
from db.ORMs import Filter, Annotation, Document


class DocsToDB(PreviousNext):
    """Import read documents into database"""

    def __init__(self, name=None):
        super().__init__(name)
        self.dao = None
        self.dbpath = ''
        self.remove_old = False
        pass

    def start(self):
        self.dao = self.workflow.dao
        self.dbpath = self.workflow.dbpath
        with self.workflow.dao.create_session() as session:
            num_docs = session.query(func.count(Document.doc_id)).first()
            if num_docs is not None and num_docs[0] > 0:
                self.displayOptions(num_docs[0])
            else:
                self.importData()
                self.next_step.start()
        pass

    def updateBox(self):
        rows = [self.html, self.toggle] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox

    def displayOptions(self, num_docs):
        clear_output()
        self.html = widgets.HTML(
            '<h4>There are %s document  database exists, do you want to overwrite?</h4>' % (num_docs))
        self.toggle = widgets.ToggleButtons(
            options=['Yes', 'No'],
            description='',
            disabled=False,
            value='No',
            button_style='',  # 'success', 'info', 'warning', 'danger' or ''
            tooltips=['Replace the old database', 'Append data to the old database'],
            layout=widgets.Layout(width='70%')
            #     icons=['check'] * 3
        )
        self.toggle.observe(self.on_click, 'value')
        # pad the descriptions list if it is shorter than options list
        self.resetParameters()
        self.box = self.updateBox()
        display(self.box)
        pass

    def on_click(self, change):
        self.data = change['new']
        if self.data == 'Yes':
            self.remove_old = True
        pass

    def complete(self):
        clear_output(True)
        if self.remove_old:
            os.remove(self.dbpath)
            self.createSQLTables()
        self.importData()
        if self.next_step is not None:
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

    def createSQLTables(self):
        Model.metadata.create_all(bind=self.dao._engine)
        pass

    def importData(self):
        if hasattr(self.previous_step, 'data') and self.previous_step.data is not None:
            self.parseData(self.previous_step.data)
            self.previous_step.data.to_sql('document', self.dao._engine.raw_connection(),
                                           if_exists='append')
        if isinstance(self.workflow.steps[1], PreviousNextText) and self.workflow.steps[
            1].data is not None and isinstance(self.workflow.steps[1].data, str):
            task_name = self.workflow.steps[1].data
            with self.dao.create_session() as session:
                res = session.query(Task).filter(Task.task_name == task_name).first()
                if res is None:
                    session.add(Task(task_name=task_name))

        pass

    def parseData(self, df):
        """dataset specific, parse meta-data from the existing columns"""
        if not 'bunch_id' in self.previous_step.data.columns:
            df.insert(1, 'bunch_id', [name.split('_')[0] for name in df.index], allow_duplicates=True)
            df['date'] = df.apply(lambda row: row.text[13:row.text.find('\n')].strip(), axis=1)
            df['dataset_id'] = df.apply(lambda row: 'origin_doc', axis=1)
        pass
