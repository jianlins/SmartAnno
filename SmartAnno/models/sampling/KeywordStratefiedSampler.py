import os
import random
import re
from sqlalchemy.sql import functions
from sqlalchemy import func

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Document
from SmartAnno.models.sampling.BaseSampler import BaseSampler

from whoosh.qparser import QueryParser
from whoosh.index import open_dir

from SmartAnno.utils.NoteBookLogger import logError


class KeywordStratefiedSampler(BaseSampler):
    def __init__(self, **kwargs):
        self.sample_size = 0
        self.previous_sampled_ids = kwargs['previous_sampled_ids']
        self.dao = kwargs['dao']
        self.dataset_id = 'origin_doc' if 'dataset_id' not in kwargs else kwargs['dataset_id']
        self.ignore_case = True
        self.whoosh_root = ConfigReader.getValue('whoosh/root_path')
        self.grouped_ids = dict()
        self.all_contain_ids = set()
        self.available_not_contain = 0
        self.new_available_not_contain = 0
        self.new_ids = dict()
        self.current_stats = dict()
        pass

    def getSummary(self, filters: dict = dict()) -> dict:
        """get doc_names (ids) grouped by type names, after query using type specific keywords(filters)
        :param filters: a dictionary of keywords grouped by type names
        :return: a dictionary of doc_names grouped by type names, a dictionary of doc_names that haven't been sampled grouped by type names
                 total number of documents that do not have any keywords, total number of documents that do not have any
                 keywords and have not been sampled
        :rtype: dict
        """
        ix = open_dir(os.path.join(self.whoosh_root, self.dataset_id))
        self.grouped_ids = {type_name: set() for type_name in filters.keys()}
        self.new_ids = {type_name: set() for type_name in filters.keys()}
        queries = self.__builQueries(filters)
        # use this to pull keyword_not_contained documents
        self.all_contain_ids = set()

        for type_name, query_str in queries.items():
            with ix.searcher() as searcher:
                query = QueryParser("TEXT", ix.schema).parse(query_str)
                hits = searcher.search(query, limit=5000, terms=True)
                for hit in hits:
                    doc_id = hit['DOC_ID']
                    if doc_id not in self.all_contain_ids:
                        self.grouped_ids[type_name].add(hit['DOC_ID'])
                        if doc_id not in self.previous_sampled_ids:
                            self.new_ids[type_name].add(hit['DOC_ID'])
                        self.all_contain_ids.add(doc_id)

        ix.close()
        with self.dao.create_session() as session:
            res = session.query(func.count(Document.DOC_ID)).filter(Document.DATASET_ID == self.dataset_id).scalar()
            total_available = res
            self.available_not_contain = total_available - len(self.all_contain_ids)
            self.new_available_not_contain = self.available_not_contain - \
                                             (len(self.previous_sampled_ids)
                                              - len(self.all_contain_ids.intersection(self.previous_sampled_ids)))
        self.current_stats = {'all_counts': {type_name: len(value) for type_name, value in self.grouped_ids.items()},
                              'new_counts': {type_name: len(value) for type_name, value in self.new_ids.items()}}
        self.current_stats['all_counts']['not_contain'] = self.available_not_contain
        self.current_stats['new_counts']['not_contain'] = self.new_available_not_contain
        return self.grouped_ids, self.new_ids, self.current_stats

    def __builQueries(self, filters: dict = dict()) -> dict:
        """convert keywords dictionaries into whoosh queries
        :rtype: dict
        :param filters: a dictionary of keywords grouped by type name
        :return: a dictionary of queries grouped by type name
        """
        queries = dict()
        for type_name, keywords in filters.items():
            query_builder = []
            for keyword in keywords:
                if ' ' not in keyword:
                    query_builder.append(keyword)
                else:
                    query_builder.append('(' + re.sub(r'\s+', ' AND ', keyword) + ')')
            queries[type_name] = ' OR '.join(query_builder)
        return queries

    def sampling(self, sample_size=0, grouped_ids=None, new_ids=None, current_stats=None,
                 exclude_previous_sampled_id=True,
                 filter_percent=70):
        if grouped_ids is None:
            grouped_ids = self.grouped_ids
        if new_ids is None:
            new_ids = self.new_ids
        if current_stats is None:
            current_stats = self.current_stats
        sample_sizes = self.getStratefiedSizes(current_stats, sample_size, exclude_previous_sampled_id,
                                               filter_percent)
        sampled_ids = self.samplingIds(sample_sizes, grouped_ids, new_ids, exclude_previous_sampled_id)
        print(sample_sizes)
        return self.getDocsFromSampledIds(sampled_ids, self.all_contain_ids)

    def getStratefiedSizes(self, stats, sample_size=0, exclude_previous_sampled_id=True, filter_percent=60):
        if exclude_previous_sampled_id:
            sub_stats = stats['new_counts']
        else:
            sub_stats = stats['all_counts']
        contain_size = int(1.0 * sample_size * filter_percent / 100)
        total_docs = sum(sub_stats.values())
        total_contain = total_docs - sub_stats['not_contain']
        if total_contain < contain_size:
            notcontain_size = sample_size - total_contain
            contain_size = total_contain
        else:
            notcontain_size = sample_size - contain_size
            if notcontain_size > sub_stats['not_contain']:
                contain_size = notcontain_size - sub_stats['not_contain'] + contain_size
                notcontain_size = sub_stats['not_contain']
                if contain_size > total_contain:
                    contain_size = total_contain

        average_size_for_contains = round(contain_size / (len(sub_stats) - 1))
        #
        sorted_types = sorted(sub_stats, key=lambda k: sub_stats[k])
        sorted_types.remove('not_contain')
        total_sampled_size = 0
        sampled_sizes = dict()
        for i in range(0, len(sorted_types)):
            type_name = sorted_types[i]
            if sub_stats[type_name] < average_size_for_contains:
                # if the docs in this type is smaller than expected average, sample all of them, record the total number
                #  of docs that owed for the sampling for other types to make up
                sampled_sizes[type_name] = sub_stats[type_name]
                total_sampled_size += sub_stats[type_name]
            elif sub_stats[type_name] == average_size_for_contains:
                sampled_sizes[type_name] = sub_stats[type_name]
                total_sampled_size += sub_stats[type_name]
            else:
                average_size_for_contains = round((contain_size - total_sampled_size) / (len(sorted_types) - i))
                if sub_stats[type_name] <= average_size_for_contains:
                    sampled_sizes[type_name] = sub_stats[type_name]
                    total_sampled_size += sub_stats[type_name]
                else:
                    this_size = average_size_for_contains
                    if i == len(sorted_types) - 1:
                        this_size = contain_size - total_sampled_size
                    sampled_sizes[type_name] = this_size
                    total_sampled_size += this_size
        sampled_sizes['not_contain'] = notcontain_size
        return sampled_sizes

    def getDocsFromSampledIds(self, sampled_ids, notcontain_size, all_contain_ids=None):
        if all_contain_ids is None:
            all_contain_ids = self.all_contain_ids
        grouped_docs = self.queryDocsByIds({'not_contain': all_contain_ids}, False, notcontain_size)
        grouped_docs.update(self.queryDocsByIds(sampled_ids, in_constrain=True))
        return self.spreadDocs(grouped_docs)

    def samplingIds(self, sample_sizes=None, grouped_ids=None, new_ids=None, exclude_previous_sampled_id=True):
        if sample_sizes is None:
            sample_sizes = self.sample_sizes

        if grouped_ids is None:
            grouped_ids = self.grouped_ids

        if new_ids is None:
            new_ids = self.new_ids

        ids_pools = new_ids if exclude_previous_sampled_id else grouped_ids
        sampled_ids = dict()
        for type_name, ids in ids_pools.items():
            # if all ids need to be sampled, not need to shuffle
            sampled_ids[type_name] = list(ids_pools[type_name])
            # otherwise, shuffle to make random sampling
            if sample_sizes[type_name] < len(ids_pools[type_name]):
                random.shuffle(sampled_ids[type_name])
                sampled_ids[type_name] = sampled_ids[type_name][: sample_sizes[type_name]]

        # for not-contain-keywords documents, there is no id pulled yet. Need do it in the next step,
        # where sampling directly done when query the database
        return sampled_ids

    def queryDocsByIds(self, grouped_ids, in_constrain=True, limit_to=-1):
        counter = 0
        reverse_groups = dict()
        for type_name, ids in grouped_ids.items():
            for one_id in ids:
                reverse_groups[one_id] = type_name
        default_type = ''
        if not in_constrain:
            default_type = list(grouped_ids.keys())[0]
        grouped_docs = {type_name: [] for type_name, id in grouped_ids.items()}
        with self.dao.create_session() as session:
            if not in_constrain:
                doc_iter = session.query(Document).filter(Document.DATASET_ID == self.dataset_id).order_by(
                    functions.random())
                for doc in doc_iter:
                    if (doc.DOC_ID not in grouped_ids):
                        grouped_docs[default_type].append(
                            Document(doc.DOC_ID, doc.DATASET_ID, doc.BUNCH_ID, doc.DOC_NAME, doc.TEXT, doc.DATE,
                                     doc.REF_DATE, doc.META_DATA))
                        counter += 1
                    if 0 < limit_to <= counter:
                        break
            else:
                for type_name, ids in grouped_ids.items():
                    for doc_id in ids:
                        doc = session.query(Document).filter(Document.DATASET_ID == self.dataset_id).filter(
                            Document.DOC_ID == doc_id).first()
                        if doc is None:
                            logError(
                                'Oops, it seems a DOC_ID ({}) does not exist in the database, you may need to rebuild the whoosh index'.format(
                                    doc_id))
                        else:
                            grouped_docs[type_name].append(doc.clone())
        return grouped_docs

    def spreadDocs(self, grouped_docs):
        """try evenly spread the sampled documents by type_names in order, so that when doing the annotation, the
        different types of documents will be displayed sequentially"""
        docs = []
        types = grouped_docs.keys()
        pointer = {type_name: 0 for type_name in grouped_docs.keys()}
        finished_types = []
        while len(finished_types) < len(grouped_docs):
            for type_name in types:
                if type_name in finished_types:
                    continue
                current_pointer = pointer[type_name]
                if current_pointer < len(grouped_docs[type_name]):
                    docs.append(grouped_docs[type_name][current_pointer])
                    pointer[type_name] += 1
                else:
                    finished_types.append(type_name)
        return docs
