import os

import sqlalchemy_dao
from IPython.core.display import clear_output, display
from ipywidgets import widgets
from sqlalchemy_dao import Dao
from sqlalchemy_dao import Model

from conf.ConfigReader import ConfigReader
from gui.PreviousNextWidgets import PreviousNext, PreviousNextText
from gui.Workflow import Step

from db.ORMs import Task, Typedef
from db.ORMs import Filter, Annotation, Document


class DBInitiater(PreviousNext):
    """Import read documents into database"""

    def __init__(self, name=None):
        super().__init__(name)
        self.dao = None
        self.dbfile = ''
        self.dbpath = ''
        self.need_import = False
        pass

    def start(self):
        if not hasattr(self.workflow, 'dao') or self.workflow.dao is None:
            print(self.workflow.config_file)
            self.dbfile = ConfigReader(self.workflow.config_file).getValue('db')
            self.dbpath = self.dbfile[self.dbfile.find(':///') + 4:]
            if os.path.isfile(self.dbpath):
                self.initDao(self.dbfile)
                self.displayOptions()
            else:
                self.initDao(self.dbfile)
                self.createSQLTables()
                self.need_import = True
                self.next_step.start()
        else:
            self.next_step.start()
        pass

    def backStart(self):
        self.workflow.dao = None
        self.start()
        pass

    def updateBox(self):
        rows = [self.html, self.toggle] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox

    def initDao(self, dbfile):
        self.dao = Dao(self.dbfile, sqlalchemy_dao.POOL_DISABLED)
        self.workflow.dao = self.dao
        self.workflow.dbpath = self.dbfile[self.dbfile.find(':///') + 4:]
        pass

    def displayOptions(self):
        clear_output()
        self.html = widgets.HTML('<h4>Sqlite database "%s" exists, do you want to overwrite?</h4>' % self.dbpath)
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
            self.need_import = True
        pass

    def complete(self):
        clear_output(True)
        if self.need_import:
            os.remove(self.dbpath)
            self.dao = Dao(self.dbfile, sqlalchemy_dao.POOL_DISABLED)
            self.createSQLTables()
        else:
            self.dao = Dao(self.dbfile, sqlalchemy_dao.POOL_DISABLED)
        self.workflow.dao = self.dao
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
