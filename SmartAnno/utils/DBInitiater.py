import os

import sqlalchemy_dao
from IPython.core.display import clear_output, display
from ipywidgets import widgets
from sqlalchemy_dao import Dao
from sqlalchemy_dao import Model

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.gui.PreviousNextWidgets import PreviousNext
from SmartAnno.gui.Workflow import Step


class DBInitiater(PreviousNext):
    """Import read documents into database"""

    def __init__(self, name=None):
        super().__init__(name)
        self.dao = None
        self.db_config = ''
        self.dbpath = ''
        self.need_import = False
        self.overwrite = False
        pass

    def start(self):
        if not hasattr(self.workflow, 'dao') or self.workflow.dao is None:
            print(self.workflow.config_file)
            self.dbpath = ConfigReader(self.workflow.config_file).getValue('db_path')
            self.db_config = ConfigReader(self.workflow.config_file).getValue('db_header') + self.dbpath

            if os.path.isfile(self.dbpath):
                self.initDao(self.db_config)
                self.displayOptions()
            else:
                self.initDao(self.db_config)
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
        rows = [self.html, self.toggle] + self.addSeparator(top='10px') + \
               [self.html2, self.toggle2] + self.addSeparator(top='10px') + [
                   self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        return vbox

    def initDao(self, dbfile):
        self.dao = Dao(self.db_config, sqlalchemy_dao.POOL_DISABLED)
        self.workflow.dao = self.dao
        self.workflow.dbpath = self.db_config[self.db_config.find(':///') + 4:]
        pass

    def displayOptions(self):
        clear_output()
        self.html = widgets.HTML(
            '<h4>Sqlite database "%s" exists, do you want to overwrite?</h4>'
            '<h4>choose <b>yes</b> will <span style="color:red"><b>clear all the data</b></span> in that database file</h4>' % self.dbpath)
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
        self.html2 = widgets.HTML(
            '<h4>Do you want to import new data?</h4>')
        self.toggle2 = widgets.ToggleButtons(
            options=['Yes', 'No'],
            description='',
            disabled=False,
            value='No',
            button_style='',  # 'success', 'info', 'warning', 'danger' or ''
            tooltips=['Add new data to db', 'Use existing data in db'],
            layout=widgets.Layout(width='70%')
        )

        # pad the descriptions list if it is shorter than options list
        self.resetParameters()
        self.box = self.updateBox()
        display(self.box)
        pass

    def on_click(self, change):
        self.data = change['new']
        if self.data == 'Yes':
            self.toggle2.value = 'Yes'
        pass

    def complete(self):
        clear_output(True)
        if self.toggle.value == 'Yes':
            os.remove(self.dbpath)
            self.dao = Dao(self.db_config, sqlalchemy_dao.POOL_DISABLED)
            self.createSQLTables()
            self.overwrite = True
            self.need_import = True
        else:
            self.dao = Dao(self.db_config, sqlalchemy_dao.POOL_DISABLED)
            if self.toggle2.value == 'Yes':
                self.need_import = True
            self.overwrite = False
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
