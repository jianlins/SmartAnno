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
    doc_id = Column(Integer, primary_key=True)
    # bunch can be used to represent a visit or a patient for a bunch of documents belows
    # to a same unit
    dataset_id = Column(String, index=True)
    bunch_id = Column(String, index=True)
    doc_name = Column(String, index=True)
    text = Column(CLOB)
    date = Column(Date, default=datetime.datetime.utcnow)
    meta_data = Column(String)

    def __repr__(self):
        return "<Document(doc_id='%s', bunch_id='%s', doc_name='%s',text='%s',date='%s', meta_data='%s')>" % (
            self.doc_id, self.bunch_id, self.doc_name, self.text, self.date, self.meta_data)


class Annotation(Model):
    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey("document.doc_id"))
    task_id = Column(String, ForeignKey("task.id"))
    run_id = Column(String, index=True)
    type = Column(String, ForeignKey("typedef.type_name"))
    reviewed_type = Column(String, ForeignKey("typedef.type_name"))
    begin = Column(Integer)
    end = Column(Integer)
    snippet_begin = Column(Integer)
    text = Column(String)
    snippet = Column(String)
    features = Column(String)
    comments = Column(String)
    create_dtm = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<Annotation(id='%s', doc_id='%s'," \
               " run_id='%s',type='%s',begin='%s', end='%s'," \
               "snippet_begin='%s', text='%s',snippet='%s'," \
               "features='%s',comments='%s',create_dtm='%s')>" % (
                   self.id, self.doc_id, self.run_id,
                   self.type, self.begin, self.end, self.snippet_begin,
                   self.text, self.snippet, self.features, self.comments,
                   self.create_dtm)


class Filter(Model):
    id = Column(Integer, primary_key=True)
    task_id = Column(String, ForeignKey("task.id"))
    keyword = Column(String)
    type_name = Column(String, ForeignKey("typedef.type_name"))

    def __repr__(self):
        return "<Filter(id='%s', task_id='%s'," \
               " keyword='%s',type_name='%s')>" % (self.id, self.task_id, self.keyword, self.type_name)
