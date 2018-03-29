import datetime

from sqlalchemy import Column, Integer, String, Table, MetaData, Date, DateTime, ForeignKey, Text, CLOB
from sqlalchemy_dao import Model, Dao


class Task(Model):
    id = Column(Integer, primary_key=True)
    task_name = Column(String, index=True)

    def __repr__(self):
        return "<Task (id='%s', task_name='%s')>" % (self.id, self.task_name)


class Typedef(Model):
    id = Column(Integer, primary_key=True)
    type_name = Column(String, index=True)
    task_id = Column(String, ForeignKey("task.id"))

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
        return "<Document(DOC_ID='%s', BUNCH_ID='%s', DOC_NAME='%s',TEXT='%s',DATE='%s', REF_DATE='%s',META_DATA='%s')>" % (
            self.DOC_ID, self.BUNCH_ID, self.DOC_NAME, self.TEXT, self.DATE, self.REF_DATE, self.META_DATA)

    def clone(self):
        return Document()


class Annotation(Model):
    ID = Column(Integer, primary_key=True)
    DOC_ID = Column(Integer, ForeignKey("document.DOC_ID"))
    TASK_ID = Column(String, ForeignKey("task.id"))
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
        return "<Annotation(id='%s', doc_id='%s'," \
               " run_id='%s',type='%s',begin='%s', end='%s'," \
               "snippet_begin='%s', text='%s',snippet='%s'," \
               "features='%s',comments='%s',create_dtm='%s')>" % (
                   self.ID, self.DOC_ID, self.RUN_ID,
                   self.TYPE, self.BEGIN, self.END, self.SNIPPET_BEGIN,
                   self.TEXT, self.SNIPPET, self.FEATURES, self.COMMENTS,
                   self.CREATE_DTM)


class Filter(Model):
    id = Column(Integer, primary_key=True)
    task_id = Column(String, ForeignKey("task.id"))
    keyword = Column(String)
    # differentiate user input or umls extended ('umls') or word embedding extended ('woem')
    type = Column(String, default='orig')
    type_name = Column(String, ForeignKey("typedef.type_name"))

    def __repr__(self):
        return "<Filter(id='%s', task_id='%s'," \
               " keyword='%s',type_name='%s')>" % (self.id, self.task_id, self.keyword, self.type_name)
