from collections import OrderedDict
from pathlib import Path

import faiss
import numpy as np

from SmartAnno.db.ORMs import Document, Annotation
from SmartAnno.models.sampling.KeywordStratefiedSampler import KeywordStratefiedSampler
from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.utils.NoteBookLogger import logError


class UniversalSentenceEncoderStratefiedSampler(KeywordStratefiedSampler):
    VECTOR_DUMP = 'vec_dump.pickle'
    FAISS_INX = 'faiss_idx.index'

    def __init__(self, **kwargs):
        self.sample_size = 0
        self.previous_sampled_ids = kwargs['previous_sampled_ids']
        self.dao = kwargs['dao']
        self.task_id = kwargs['task_id']
        self.dataset_id = 'origin_doc' if 'dataset_id' not in kwargs else kwargs['dataset_id']
        self.ignore_case = True
        self.whoosh_root = ConfigReader.getValue('whoosh/root_path')
        self.grouped_ids = dict()
        self.all_contain_ids = set()
        self.available_not_contain = 0
        self.new_available_not_contain = 0
        self.new_ids = dict()
        self.current_stats = dict()
        if 'index_dir' in kwargs:
            self.index_dir = kwargs['index_dir']
        else:
            self.index_dir = 'data/faiss'
        self.dataset_idx = OrderedDict()
        self.dataset_txt = []
        self.dataset_doc_ids = []
        pass

    def getSummary(self, filters: dict = dict(), reindex=False, distance_threhold=1) -> dict:
        """get doc_names (ids) grouped by distance to previous annotated categories
        :param filters: a dictionary of keywords grouped by type names
        :return: a dictionary of doc_names grouped by type names, a dictionary of doc_names that haven't been sampled grouped by type names
                 total number of documents that do not have any keywords, total number of documents that do not have any
                 keywords and have not been sampled
        :rtype: dict
        """
        annos = dict()
        self.grouped_ids = {type_name: set() for type_name in filters.keys()}
        self.new_ids = {type_name: set() for type_name in filters.keys()}
        with self.dao.create_session() as session:
            res = session.query(Annotation).filter(Annotation.TASK_ID == self.task_id, Annotation.REVIEWED_TYPE != None)
            for anno in res:
                if anno.REVIEWED_TYPE not in annos:
                    annos[anno.REVIEWED_TYPE] = set()
                annos[anno.REVIEWED_TYPE].add(anno.DOC_ID)

        # read dataset from database
        if reindex or len(self.dataset_idx) == 0:
            self.dataset_idx.clear()
            self.dataset_txt.clear()
            with self.dao.create_session() as session:
                res = session.query(Document).filter(Document.DATASET_ID == self.dataset_id)
                for doc in res:
                    self.dataset_idx[doc.DOC_ID] = len(self.dataset_txt)
                    self.dataset_txt.append(doc.TEXT)
                    self.dataset_doc_ids.append(doc.DOC_ID)

        if reindex or not Path(self.index_dir, self.VECTOR_DUMP).is_file():
            print('Start reindexing sentence embeddings...')
            import tensorflow as tf
            import tensorflow_hub as hub

            module_url = "https://tfhub.dev/google/universal-sentence-encoder-large/3"
            embed = hub.Module(module_url)
            print('Sentence encoder model loaded.')

            # need to split the dataset to fit into memory for sentence encoder
            dataset_embeddings = None
            i = 0
            pace = 1000
            print('Start encoding documents...')
            while i <= (len(self.dataset_txt) - pace) / pace:
                with tf.Session() as session:
                    session.run([tf.global_variables_initializer(), tf.tables_initializer()])
                    if dataset_embeddings is None:
                        dataset_embeddings=session.run(embed(self.dataset_txt[i * pace:(i + 1) * pace]))
                    else:
                        dataset_embeddings = np.concatenate(
                        [dataset_embeddings, session.run(embed(self.dataset_txt[i * pace:(i + 1) * pace]))])
                print(str(i*pace)+' documents have been encoded.')
                i += 1

            if i * pace < len(self.dataset_txt):
                if dataset_embeddings is None:
                    dataset_embeddings = session.run(embed(self.dataset_txt[i * pace:(i + 1) * pace]))
                else:
                    dataset_embeddings = np.concatenate(
                        [dataset_embeddings, session.run(embed(self.dataset_txt[i * pace:]))])

            if dataset_embeddings is None:
                logError('dataset_embeddings is none, no documents were read from the database.')
                return
            dimension = dataset_embeddings.shape[1]
            # save vectors
            dataset_embeddings.dump(Path(self.index_dir, self.VECTOR_DUMP))
            print('Sentence embedding generated.')

            faiss_index = faiss.IndexFlatL2(dimension)
            faiss_index.add(dataset_embeddings)
            # save faiss index
            faiss.write_index_binary(faiss_index, str(Path(self.index_dir, self.FAISS_INX)))
            print('Sentence embedding indexed.')
        else:
            print('Loading indexed sentence embeddings and faiss indexes...')
            dataset_embeddings = np.load(Path(self.index_dir, self.VECTOR_DUMP))
            faiss_index = faiss.read_index_binary(str(Path(self.index_dir, self.FAISS_INX)))
        return self.gen_stats(self.dataset_idx, self.dataset_doc_ids, dataset_embeddings, faiss_index, annos,
                              distance_threhold)

    def gen_stats(self, dataset_idx: OrderedDict, dataset_doc_ids: object, dataset_embeddings: object,
                  faiss_index: object,
                  annos: object, distance_threhold: float) -> (dict, dict, dict):
        """
        :param dataset_idx:  The dictionary to map document id to the index in dataset_doc_ids
        :param dataset_doc_ids: Array of document ids
        :param dataset_embeddings: Numpy array of document embeddings
        :param faiss_index:    Faiss index
        :param annos:   The dictionary to map each annotation type to a set of document ids.
        :return: A dictionary group document ids by annotation type, a dictionary group not sampled document ids
        by annotation type, a stats counts for each annotation type.
        """
        distances = {type_name: dict() for type_name in self.grouped_ids.keys()}
        for type_name, docs in annos.items():
            subset_embeddings = np.array([dataset_embeddings[dataset_idx[doc_id]] for doc_id in docs])
            D, I = faiss_index.search(subset_embeddings, int(len(dataset_embeddings) * 0.8))
            for i in range(0, len(D)):
                res_d = D[i]
                if res_d > distance_threhold:
                    break
                doc_id = dataset_doc_ids[i]
                self.grouped_ids[type_name].add(doc_id)
                # update the distances of a candidate doc to the closest doc in the reviewed documents
                if doc_id not in distances[type_name] or res_d < distances[type_name][doc_id]:
                    distances[type_name][doc_id] = res_d

        # solve overlapping candidates
        for doc_id in dataset_doc_ids:
            shortest_distance = 10000
            to_remove_from_types = []
            previous_type = ''
            for type_name in distances.keys():
                if distances[type_name][doc_id] < shortest_distance:
                    shortest_distance = distances[type_name][doc_id]
                    if previous_type != '':
                        to_remove_from_types.append(type_name)
                    previous_type = type_name

            for type_name in to_remove_from_types:
                self.grouped_ids[type_name].remove(doc_id)

        available_outscope_ids = set(dataset_doc_ids)
        # identify the documents haven't been reviewed
        for type_name, doc_ids in self.grouped_ids.items():
            available_outscope_ids = available_outscope_ids - doc_ids
            self.new_ids[type_name] = doc_ids - self.previous_sampled_ids

        self.current_stats = {'all_counts': {type_name: len(value) for type_name, value in self.grouped_ids.items()},
                              'new_counts': {type_name: len(value) for type_name, value in self.new_ids.items()}}

        self.available_not_contain = len(available_outscope_ids)
        self.current_stats['all_counts']['not_contain'] = self.available_not_contain
        self.new_available_not_contain = len(available_outscope_ids - self.previous_sampled_ids)
        self.current_stats['new_counts']['not_contain'] = self.new_available_not_contain
        return self.grouped_ids, self.new_ids, self.current_stats
