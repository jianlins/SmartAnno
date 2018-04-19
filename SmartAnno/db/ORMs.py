import datetime

from sqlalchemy import Column, Integer, String, Table, MetaData, Date, DateTime, ForeignKey, Text, CLOB
from sqlalchemy_dao import Model, Dao


class Task(Model):
    ID = Column(Integer, primary_key=True)
    TASK_NAME = Column(String, index=True)
    DATASET_ID = Column(String, index=True)

    def __repr__(self):
        return "<Task (ID='%s', TASK_NAME='%s, DATASET_ID='%s'')>" % (self.ID, self.TASK_NAME, self.DATASET_ID)


class Typedef(Model):
    id = Column(Integer, primary_key=True)
    type_name = Column(String, index=True)
    task_id = Column(String, ForeignKey("task.ID"))

    def __repr__(self):
        return "<TypeDef (id='%s', type_name='%s',type_group_id='%s')>" % (self.id, self.type_name, self.task_id)


class Document(Model):
    DOC_ID = Column(Integer, primary_key=True)
    # bunch can be used to represent a visit or a patient for a bunch of documents belows
    # to a same unit
    DATASET_ID = Column(String, index=True)
    BUNCH_ID = Column(String, index=True)
    DOC_NAME = Column(String, index=True)
    TEXT = Column(CLOB)
    DATE = Column(Date, default=datetime.datetime.utcnow)
    REF_DATE = Column(Date, default=datetime.datetime.utcnow)
    META_DATA = Column(String)

    def __init__(self, DOC_ID, DATASET_ID, BUNCH_ID, DOC_NAME, TEXT, DATE, REF_DATE, META_DATA):
        self.DOC_ID = DOC_ID
        self.DATASET_ID = DATASET_ID
        self.BUNCH_ID = BUNCH_ID
        self.DOC_NAME = DOC_NAME
        self.TEXT = TEXT
        self.DATE = DATE
        self.REF_DATE = REF_DATE
        self.META_DATA = META_DATA

    def __repr__(self):
        return "<Document(DOC_ID='%s',DATASET_ID='%s', BUNCH_ID='%s', DOC_NAME='%s',TEXT='%s',DATE='%s', REF_DATE='%s',META_DATA='%s')>" % (
            self.DOC_ID, self.DATASET_ID, self.BUNCH_ID, self.DOC_NAME, self.TEXT, self.DATE, self.REF_DATE,
            self.META_DATA)

    def clone(self):
        return Document(self.DOC_ID, self.DATASET_ID, self.BUNCH_ID, self.DOC_NAME, self.TEXT, self.DATE,
                        self.REF_DATE, self.META_DATA)


class Annotation(Model):
    ID = Column(Integer, primary_key=True)
    BUNCH_ID = Column(String, ForeignKey("document.BUNCH_ID"))
    DOC_ID = Column(Integer, ForeignKey("document.DOC_ID"))
    TASK_ID = Column(String, ForeignKey("task.ID"))
    RUN_ID = Column(String, index=True)
    TYPE = Column(String, ForeignKey("typedef.type_name"))
    REVIEWED_TYPE = Column(String, ForeignKey("typedef.type_name"))
    BEGIN = Column(Integer)
    END = Column(Integer)
    SNIPPET_BEGIN = Column(Integer)
    TEXT = Column(String)
    SNIPPET = Column(String)
    FEATURES = Column(String)
    COMMENTS = Column(String)
    CREATE_DTM = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<Annotation(ID='%s', BUNCH_ID='%s',DOC_ID='%s'," \
               " RUN_ID='%s',TYPE='%s',REVIEWED_TYPE='%s',BEGIN='%s', END='%s'," \
               "SNIPPET_BEGIN='%s', TEXT='%s',SNIPPET='%s'," \
               "FEATURES='%s',COMMENTS='%s',CREATE_DTM='%s')>" % (
                   self.ID, self.BUNCH_ID, self.DOC_ID, self.RUN_ID,
                   self.TYPE, self.REVIEWED_TYPE, self.BEGIN, self.END, self.SNIPPET_BEGIN,
                   self.TEXT, self.SNIPPET, self.FEATURES, self.COMMENTS,
                   self.CREATE_DTM)

    def clone(self):
        return Annotation(ID=self.ID, BUNCH_ID=self.BUNCH_ID, DOC_ID=self.DOC_ID, TASK_ID=self.TASK_ID,
                          RUN_ID=self.RUN_ID,
                          TYPE=self.TYPE, REVIEWED_TYPE=self.REVIEWED_TYPE,
                          BEGIN=self.BEGIN, END=self.END,
                          SNIPPET_BEGIN=self.SNIPPET_BEGIN, TEXT=self.TEXT,
                          SNIPPET=self.SNIPPET, FEATURES=self.FEATURES,
                          COMMENTS=self.COMMENTS, CREATE_DTM=self.CREATE_DTM)


class Filter(Model):
    id = Column(Integer, primary_key=True)
    task_id = Column(String, ForeignKey("task.ID"))
    keyword = Column(String)
    # differentiate user input or umls extended ('umls') or word embedding extended ('woem')
    type = Column(String, default='orig')
    type_name = Column(String, ForeignKey("typedef.type_name"))

    def __repr__(self):
        return "<Filter(id='%s', task_id='%s'," \
               " keyword='%s',type_name='%s')>" % (self.id, self.task_id, self.keyword, self.type_name)


def saveDFtoDB(dao, df, table_name):
    '''pandas dataframe to_sql often throw index error, use this to work around'''
    listToWrite = df.to_dict(orient='records')
    import sqlalchemy
    metadata = sqlalchemy.schema.MetaData(bind=dao._engine, reflect=True)
    table = sqlalchemy.Table(table_name, metadata, autoload=True)
    # Open the session
    session = dao.create_session()
    # Inser the dataframe into the database in one bulk
    conn = dao._engine.connect()
    conn.execute(table.insert(), listToWrite)
    session.commit()
    session.close()
