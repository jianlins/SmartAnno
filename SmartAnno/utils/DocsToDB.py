import sqlalchemy_dao
from sqlalchemy_dao import Dao
from conf.ConfigReader import ConfigReader
from gui.PreviousNextWidgets import PreviousNext


class DocsToDB(PreviousNext):
    """Import read documents into database"""

    def __init__(self, name=None):
        super().__init__(name)
        self.dao = None
        pass

    def start(self):
        if not hasattr(self.workflow, 'dao') or self.workflow.dao is None:
            dbfile = ConfigReader(self.workflow.config_file).getValue('db')
            self.workflow.dao = Dao(dbfile, sqlalchemy_dao.POOL_DISABLED)
            self.dao = self.workflow.dao
        if hasattr(self.previous_step, 'data') and self.previous_step.data is not None:
            self.parseData(self.previous_step.data)
            self.previous_step.data.to_sql('document', self.dao._engine.raw_connection(), flavor='sqlite',
                                           if_exists='append')
        self.next_step.start()

    def parseData(self, df):
        if not 'bunch_id' in self.previous_step.data.columns:
            df.insert(1, 'bunch_id', [name.split('_')[0] for name in df.index], allow_duplicates=True)
            df['date'] = df.apply(lambda row: row.text[13:row.text.find('\n')].strip(), axis=1)
            df['dataset_id'] = df.apply(lambda row: 'origin_doc', axis=1)
        pass
