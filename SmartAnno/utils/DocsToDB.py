import os

from IPython.core.display import clear_output, display
from PyRuSH.RuSH import RuSH
from ipywidgets import widgets
from sqlalchemy_dao import Model
from textblob import TextBlob

from conf.ConfigReader import ConfigReader
from db.ORMs import Task, saveDFtoDB
from gui.PreviousNextWidgets import PreviousNext, PreviousNextText
from gui.Workflow import Step


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
        self.updateBox()
        display(self.box)

        # self.complete()
        # with self.workflow.dao.create_session() as session:
        #     num_docs = session.query(func.count(Document.DOC_ID)).first()
        #     if num_docs is not None and num_docs[0] > 0:
        #         self.displayOptions(num_docs[0])
        #     else:
        #         self.importData()
        #         self.next_step.start()
        pass

    def updateBox(self):
        self.html1 = widgets.HTML(
            '<h4>Give a name for this dataset: </h4>')
        self.dataset_name_input = widgets.Text(value=self.previous_step.dataset_name)
        self.dataset_name_input.observe(self.updateDateSetName, type='change')
        self.html2 = widgets.HTML(
            '<h4>Do you want to split documents into sentences for annotating?</h4><p>The sentences will be imported '
            'into dataset: <b>"{}_sents"</b></p>'.format(self.dataset_name_input.value))
        self.toggle = widgets.ToggleButtons(
            options=['TextBlob_Splitter', 'PyRuSh', 'Not_To_Split'],
            description='',
            disabled=False,
            value='Not_To_Split',
            button_style='',  # 'success', 'info', 'warning', 'danger' or ''
            tooltips=['Use TextBlob sentence splitter', 'Use PyRuSH to split sentences', 'don\'t split'],
            layout=widgets.Layout(width='70%')
            #     icons=['check'] * 3
        )
        rows = [self.html1, self.dataset_name_input, self.html2, self.toggle] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        self.box = vbox

    def updateDateSetName(self, fil):
        if len(fil['new']) > 0 and fil['new'] != fil['old']:
            if type(fil['new']) is dict:
                new_name = fil['new']['value']
            else:
                new_name = fil['new']
            self.html2.value = '<h4>Do you want to split documents into sentences for annotating?</h4><p>' \
                               'The sentences will be imported into dataset: <b>"{}_sents"</b></p>'.format(
                new_name)
        pass

    def complete(self):
        clear_output(True)
        db_initiater = self.workflow.getStepByName('db_initiater')
        if db_initiater.overwrite:
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
            # self.previous_step.data.to_sql('document', self.dao._engine.raw_connection(),
            #                                if_exists='append')
            df = self.previous_step.data
            df['DATASET_ID'] = self.dataset_name_input.value
            saveDFtoDB(self.workflow.dao, df, 'document')

        if self.toggle.value == 'TextBlob_Splitter':
            df['DATASET_ID'] = self.dataset_name_input.value + '_sents'
            self.saveSentences(self.workflow.dao, df, 'document', self.textblobSplitter)
        elif self.toggle.value == 'PyRuSh':
            df['DATASET_ID'] = self.dataset_name_input.value + '_sents'
            self.saveSentences(self.workflow.dao, df, 'document', self.pyRuSHSplitter)

        if hasattr(self.previous_step, 'references') and self.previous_step.references is not None:
            saveDFtoDB(self.workflow.dao, self.previous_step.references, 'annotation')

        if isinstance(self.workflow.steps[1], PreviousNextText) and self.workflow.steps[
            1].data is not None and isinstance(self.workflow.steps[1].data, str):
            task_name = self.workflow.task_name
            with self.dao.create_session() as session:
                res = session.query(Task).filter(Task.task_name == task_name).first()
                if res is None:
                    session.add(Task(task_name=task_name))
                    res = session.query(Task).filter(Task.task_name == task_name).first()
                self.workflow.task_id = res.id

        pass

    def saveSentences(self, dao, df, table_name, split_func):
        import pandas as pd
        sents_df = pd.DataFrame(columns=['BUNCH_ID', 'DOC_NAME', 'TEXT', 'DATE', 'REF_DATE'])
        progressbar = widgets.IntProgress(min=0, max=len(df), value=0, layout=widgets.Layout(width='50%'),
                                          description='Splitting:')
        progressbar.value = 0
        display(progressbar)
        for idx, row in df.iterrows():
            bunch_id = row['BUNCH_ID']
            doc_name = row['DOC_NAME']
            text = row['TEXT']
            date = row['DATE']
            ref_date = row['REF_DATE']
            sentence_id = 0
            progressbar.value += 1
            for sentence in split_func(text):
                sentence_id += 1
                sents_df.loc[len(sents_df)] = [bunch_id, doc_name + "_" + str(sentence_id), sentence, date, ref_date]
        saveDFtoDB(dao, sents_df, table_name)
        pass

    def textblobSplitter(self, text):
        blob = TextBlob(text)
        return [s.string.strip() for s in blob.sentences]

    def pyRuSHSplitter(self, text):
        rush = RuSH(ConfigReader.getValue('rush_rules_path'))
        sentences = rush.segToSentenceSpans(text)
        return [text[sentence.begin:sentence.end].strip() for sentence in sentences]

    def parseData(self, df):
        """dataset specific, parse meta-data from the existing columns"""
        if not 'DATASET_ID' in self.previous_step.data.columns:
            # df.insert(1, 'bunch_id', [name.split('_')[0] for name in df.index], allow_duplicates=True)
            # df['date'] = df.apply(lambda row: row.text[13:row.text.find('\n')].strip(), axis=1)
            df['DATASET_ID'] = df.apply(lambda row: self.previous_step.dataset_name, axis=1)
        pass
