import random

from sqlalchemy import or_

from db.ORMs import Document
from gui.Workflow import logConsole
from models.sampling.BaseSampler import BaseSampler


class KeywordStratefiedSampler(BaseSampler):
    def __init__(self, **kwargs):
        self.sample_size = 0
        self.filter_percent = kwargs['filter_percent']
        self.stratefied_sets = kwargs['stratefied_sets']
        self.exclusions = kwargs['exclusions']
        self.adjusted_sample_size = self.sample_size
        self.adjusted_filter_percent = self.filter_percent
        self.dao = kwargs['dao']
        pass

    def sampling(self, sample_size=0):
        if sample_size == 0:
            return super().sampling()
        self.sample_size = sample_size
        random.shuffle(self.stratefied_sets['contain'])
        random.shuffle(self.stratefied_sets['notcontain'])
        contain_size = int(self.sample_size * self.filter_percent)
        notcontain_size = self.sample_size - contain_size
        if contain_size > len(self.stratefied_sets['contain']):
            contain_size = len(self.stratefied_sets['contain'])
            notcontain_size = self.sample_size - contain_size
            logConsole(
                'Sampling adjustment: not enough samples that contain the filter keywords, reduce the contain_size to ' + str(
                    contain_size) + '; and notcontain_size has been adjusted to ' + str(notcontain_size))
        if notcontain_size > len(self.stratefied_sets['notcontain']):
            notcontain_size = len(self.stratefied_sets['notcontain'])
            logConsole(
                'Sampling adjustment: not enough samples that do not contain the filter keywords, reduce the notcontain_size to ' + str(
                    notcontain_size))
            logConsole(
                'Sampling adjustment: total sample size has been adjusted to ' + str(contain_size + notcontain_size))
            logConsole(
                'Sampling adjustment: filter percentage has been adjusted to ' + str(
                    100.0 * contain_size / self.sample_size))
        self.adjusted_sample_size = contain_size + notcontain_size
        self.adjusted_filter_percent = 100.0 * contain_size / self.sample_size

        contain_docids = self.stratefied_sets['contain'][:contain_size]
        notcontain_docids = self.stratefied_sets['notcontain'][:notcontain_size]
        docs = []
        grouping = dict()

        with self.dao.create_session() as session:
            if len(self.exclusions) > 0:
                doc_iter = session.query(Document).filter(Document.DATASET_ID == 'origin_doc').filter(
                    Document.DOC_ID.notin_(self.exclusions)).filter(
                    or_(Document.DOC_ID.in_(contain_docids), Document.DOC_ID.in_(notcontain_docids)))
            else:
                doc_iter = session.query(Document).filter(Document.DATASET_ID == 'origin_doc').filter(
                    or_(Document.DOC_ID.in_(contain_docids), Document.DOC_ID.in_(notcontain_docids)))
            for doc in doc_iter:
                if doc.DOC_ID in contain_docids:
                    docs.append(
                        Document(doc.DOC_ID, doc.DATASET_ID, doc.BUNCH_ID, doc.DOC_NAME, doc.TEXT, doc.DATE,
                                 doc.REF_DATE, doc.META_DATA))
                    grouping[doc.DOC_ID] = 'contain'
                else:
                    docs.append(
                        Document(doc.DOC_ID, doc.DATASET_ID, doc.BUNCH_ID, doc.DOC_NAME, doc.TEXT, doc.DATE,
                                 doc.REF_DATE, doc.META_DATA))
                    grouping[doc.DOC_ID] = 'notcontain'
        return docs, grouping
