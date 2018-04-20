import os
import shutil

from IPython.core.display import clear_output, display
from PyRuSH.RuSH import RuSH
from ipywidgets import widgets
from sqlalchemy_dao import Model
from textblob import TextBlob
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh.index import create_in, open_dir
from whoosh.writing import AsyncWriter

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Task, saveDFtoDB, Document
from SmartAnno.gui.PreviousNextWidgets import PreviousNext, PreviousNextText
from SmartAnno.gui.Workflow import Step
from SmartAnno.utils.NoteBookLogger import logMsg


class DocsToDB(PreviousNext):
    """Import read documents into database"""

    def __init__(self, name=None):
        super().__init__(name)
        self.dao = None
        self.dbpath = ''
        self.remove_old = False
        self.dataset_name = 'orig'
        self.whoosh_root = ConfigReader.getValue("whoosh/root_path")
        self.html1 = widgets.HTML(
            '<h4>Give a name for this dataset: </h4>')
        self.dataset_name_input = None
        self.html2 = None
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
        self.data_step = None
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
        self.data_step = self.workflow.getStepByName('readfiles')
        self.dataset_name_input = widgets.Text(value=self.data_step.dataset_name)
        self.html2 = widgets.HTML(
            '<h4>Do you want to split documents into sentences for annotating?</h4><p>The sentences will be imported '
            'into dataset: <b>"{}_sents"</b></p>'.format(self.dataset_name_input.value))
        self.dataset_name_input.observe(self.updateDateSetName, type='change')
        rows = [self.html1, self.dataset_name_input, self.html2, self.toggle] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        self.box = vbox

    def updateDateSetName(self, fil):
        # when change the dataset name, automatically change the sentence split dataset name
        if len(fil['new']) > 0 and fil['new'] != fil['old']:
            if type(fil['new']) is dict:
                new_name = fil['new']['value']
            else:
                new_name = fil['new']
            self.html2.value = '<h4>Do you want to split documents into sentences for annotating?</h4><p>' \
                               'The sentences will be imported into dataset: <b>"{}_sents"</b></p>'.format(new_name)
        pass

    def complete(self):
        clear_output(True)
        db_initiator = self.workflow.getStepByName('db_initiator')
        overwrite = db_initiator.overwrite
        self.dataset_name = self.dataset_name_input.value.strip()
        if overwrite:
            os.remove(self.dbpath)
            self.createSQLTables()
        self.importData(overwrite)
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

    def importData(self, overwrite=False):
        if hasattr(self.data_step, 'data') and self.data_step.data is not None:
            self.parseData(self.data_step)
            # self.data_step.data.to_sql('document', self.dao._engine.raw_connection(),
            #                                if_exists='append')
            df = self.data_step.data
            df['DATASET_ID'] = self.dataset_name
            saveDFtoDB(self.workflow.dao, df, 'document')
            self.saveToWhoosh(df, self.dataset_name, overwrite)

        # choose which sentence splitter you want to use.
        if self.toggle.value == 'TextBlob_Splitter':
            self.saveSentences(self.workflow.dao, df, 'document', self.textblobSplitter, overwrite)
        elif self.toggle.value == 'PyRuSh':
            self.saveSentences(self.workflow.dao, df, 'document', self.pyRuSHSplitter, overwrite)

        if hasattr(self.data_step, 'references') and self.data_step.references is not None:
            saveDFtoDB(self.workflow.dao, self.data_step.references, 'annotation')

        if isinstance(self.workflow.steps[1], PreviousNextText) and self.workflow.steps[
            1].data is not None and isinstance(self.workflow.steps[1].data, str):
            task_name = self.workflow.task_name
            with self.dao.create_session() as session:
                res = session.query(Task).filter(Task.TASK_NAME == task_name).first()
                if res is None:
                    session.add(Task(task_name=task_name))
                    res = session.query(Task).filter(Task.TASK_NAME == task_name).first()
                self.workflow.task_id = res.id

        pass

    def saveSentences(self, dao, df, table_name, split_func, overwrite=False):
        import pandas as pd
        sents_df = pd.DataFrame(columns=['DATASET_ID', 'BUNCH_ID', 'DOC_NAME', 'TEXT', 'DATE', 'REF_DATE'])
        progressbar = widgets.IntProgress(min=0, max=len(df), value=0, layout=widgets.Layout(width='80%'),
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
                sents_df.loc[len(sents_df)] = [self.dataset_name + "_sents", bunch_id,
                                               doc_name + "_" + str(sentence_id), sentence, date, ref_date]

        saveDFtoDB(dao, sents_df, table_name)
        self.saveToWhoosh(sents_df, self.dataset_name + "_sents", overwrite)
        pass

    def textblobSplitter(self, text):
        blob = TextBlob(text)
        return [s.string.strip() for s in blob.sentences]

    def pyRuSHSplitter(self, text):
        rush = RuSH(ConfigReader.getValue('rush_rules_path'))
        sentences = rush.segToSentenceSpans(text)
        return [text[sentence.begin:sentence.end].strip() for sentence in sentences]

    def parseData(self, data_step):
        """dataset specific, parse meta-data from the existing columns"""
        if not 'DATASET_ID' in self.previous_step.data.columns:
            # df.insert(1, 'bunch_id', [name.split('_')[0] for name in df.index], allow_duplicates=True)
            # df['date'] = df.apply(lambda row: row.text[13:row.text.find('\n')].strip(), axis=1)
            data_step.data['DATASET_ID'] = data_step.data.apply(lambda row: data_step.dataset_name, axis=1)
        pass

    def saveToWhoosh(self, df, dataset_id, overwrite=False):
        # use whoosh search engine to enable full text search
        if not os.path.exists(self.whoosh_root):
            os.mkdir(self.whoosh_root)
        ws_path = os.path.join(self.whoosh_root, dataset_id)
        if not os.path.exists(ws_path):
            os.mkdir(ws_path)
            logMsg(str(os.path.abspath(ws_path)) + ' does not exist, create it to store whoosh index')
            overwrite = True
        elif overwrite:
            shutil.rmtree(ws_path)
            os.mkdir(ws_path)
        schema = Schema(DOC_ID=NUMERIC(stored=True), TEXT=TEXT)
        if overwrite:
            ix = create_in(ws_path, schema)
        else:
            ix = open_dir(ws_path)
        writer = AsyncWriter(ix)

        with self.workflow.dao.create_session() as session:
            doc_iter = session.query(Document).filter(Document.DATASET_ID == dataset_id)
            for doc in doc_iter:
                writer.add_document(DOC_ID=doc.DOC_ID, TEXT=doc.TEXT)
            writer.commit()
        pass
