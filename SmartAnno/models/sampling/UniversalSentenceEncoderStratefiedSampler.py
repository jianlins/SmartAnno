from collections import OrderedDict
from pathlib import Path

import faiss
import numpy as np

from SmartAnno.db.ORMs import Document, Annotation
from SmartAnno.models.sampling.KeywordStratefiedSampler import KeywordStratefiedSampler
from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.utils.NoteBookLogger import logError


class UniversalSentenceEncoderStratefiedSampler(KeywordStratefiedSampler):
    # document/sentence embedding dump files
    VECTOR_DUMP = 'vec_dump.pickle'
    # faiss index dump file
    FAISS_INX = 'faiss_idx.index'
    # number of results to return for each query (faiss has limits, set smaller to gain speed)
    MAX_QUERY_RES = 100
    # number of documents to encode each time (universal sentence encoder has limits)
    ENCODING_PACE = 1000

    def __init__(self, **kwargs):
        self.sample_size = 0
        self.previous_sampled_ids = kwargs['previous_sampled_ids']
        self.dao = kwargs['dao']
        self.task_id = kwargs['task_id']
        self.dataset_id = 'origin_doc' if 'dataset_id' not in kwargs else kwargs['dataset_id']
        self.ignore_case = True
        self.distance_threhold = 0.3
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
        if not Path(self.index_dir).is_dir():
            Path(self.index_dir).mkdir()
        self.dataset_idx = OrderedDict()
        self.dataset_txt = []
        self.dataset_doc_ids = []
        self.faiss_index = None
        self.dataset_embeddings = None
        pass

    def getSummary(self, filters: dict = dict(), reindex=False, distance_threhold=None) -> dict:
        """get doc_names (ids) grouped by distance to previous annotated categories
        :param filters: a dictionary of keywords grouped by type names
        :return: a dictionary of doc_names grouped by type names, a dictionary of doc_names that haven't been sampled grouped by type names
                 total number of documents that do not have any keywords, total number of documents that do not have any
                 keywords and have not been sampled
        :rtype: dict
        """
        if distance_threhold is None:
            distance_threhold = self.distance_threhold
        self.grouped_ids = {type_name: set() for type_name in filters.keys()}
        self.new_ids = {type_name: set() for type_name in filters.keys()}
        annos, self.dataset_idx, self.dataset_txt, self.dataset_doc_ids = self.read_db(reindex)
        if reindex or not Path(self.index_dir, self.VECTOR_DUMP).is_file():
            self.faiss_index, self.dataset_embeddings = self.reindex_embeddings()
        else:
            print('Loading indexed sentence embeddings and faiss indexes...')
            self.faiss_index, self.dataset_embeddings = self.load_embedding_index()
        return self.gen_stats(self.dataset_idx, self.dataset_doc_ids, self.dataset_embeddings, self.faiss_index, annos,
                              distance_threhold)

    def read_db(self, reindex: bool = False) -> (dict, dict, list, list):
        """
        get documents (based on dataset_id) and previous annotated records (based on task_id) from database
        :param reindex:
        :return:annotated document ids grouped by annotation type name, dictionary to map document id to the index of documents array,
        documents array, document ids array (map index to document id)

        """
        annos = dict()
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
        return annos, self.dataset_idx, self.dataset_txt, self.dataset_doc_ids

    def reindex_embeddings(self) -> (faiss.Index, np.ndarray):
        """
        index/reoindex document/sentence embeddings
        :return: faiss index and document/sentence embeddings
        """
        self.dataset_embeddings = self.generate_embeddings()
        dimension = self.dataset_embeddings.shape[1]
        # save vectors
        self.dataset_embeddings.dump(str(Path(self.index_dir, self.VECTOR_DUMP)))
        print('Sentence embedding generated.')

        self.faiss_index = faiss.IndexFlatL2(dimension)
        self.faiss_index.add(self.dataset_embeddings)
        # save faiss index
        faiss.write_index(self.faiss_index, str(Path(self.index_dir, self.FAISS_INX)))
        print('Sentence embedding indexed.')
        return self.faiss_index, self.dataset_embeddings

    def generate_embeddings(self) -> np.ndarray:
        """
        Generate embeddings for each document/sentence--- can be replaced with other embedding method
        :return: 2d numpy array of vectors (each row represent a document embedding)
        """
        print('Start reindexing sentence embeddings...')
        import tensorflow as tf
        import tensorflow_hub as hub

        module_url = "https://tfhub.dev/google/universal-sentence-encoder-large/3"
        embed = hub.Module(module_url)
        print('Sentence encoder model loaded.')

        # need to split the dataset to fit into memory for sentence encoder
        self.dataset_embeddings = []
        i = 0
        pace = self.ENCODING_PACE
        print('Start encoding documents...')
        with tf.Session() as session:
            session.run([tf.global_variables_initializer(), tf.tables_initializer()])
            while i <= (len(self.dataset_txt) - pace) / pace:
                self.dataset_embeddings.append(session.run(embed(self.dataset_txt[i * pace:(i + 1) * pace])))
                print(str(i * pace) + ' documents have been encoded.')
                i += 1

            if i * pace < len(self.dataset_txt):
                self.dataset_embeddings.append(session.run(embed(self.dataset_txt[i * pace:])))

        if len(self.dataset_embeddings) == 0:
            logError('dataset_embeddings is none, no documents were read from the database.')
            return np.ndarray([[]])
        self.dataset_embeddings = np.concatenate(self.dataset_embeddings)
        return self.dataset_embeddings

    def load_embedding_index(self) -> (faiss.Index, np.ndarray):
        """
        Load previous indexed embedding from dump files
        :return:
        """
        self.dataset_embeddings = np.load(str(Path(self.index_dir, self.VECTOR_DUMP)), allow_pickle=True)
        self.faiss_index = faiss.read_index(str(Path(self.index_dir, self.FAISS_INX)))
        return self.faiss_index, self.dataset_embeddings

    def gen_stats(self, dataset_idx: OrderedDict, dataset_doc_ids: [], dataset_embeddings: np.ndarray,
                  faiss_index: faiss.Index,
                  annos: dict, distance_threshold: float) -> (dict, dict, dict):
        """
        Generate count stats from the dataset, grouped by different annotation types

        :param dataset_idx:  The dictionary to map document id to the index in dataset_doc_ids
        :param dataset_doc_ids: Array of document ids
        :param dataset_embeddings: Numpy array of document embeddings
        :param faiss_index:    Faiss index
        :param annos:   The dictionary to map each annotation type to a set of document ids.
        :param distance_threshold: A threhold to exclude dislike query results
        :return: A dictionary group document ids by annotation type, a dictionary group not sampled document ids
        by annotation type, a stats counts for each annotation type.
        """
        distances = {type_name: dict() for type_name in self.grouped_ids.keys()}
        print(type(dataset_embeddings))
        max_query_res = int(len(dataset_embeddings) * 0.8)
        if max_query_res > self.MAX_QUERY_RES:
            max_query_res = self.MAX_QUERY_RES
        print('Querying similar document embeddings...')
        for type_name, doc_ids in annos.items():
            subset_embeddings = np.array([dataset_embeddings[dataset_idx[doc_id]] for doc_id in doc_ids])
            for i in range(0, len(subset_embeddings)):
                res_distances, res_doc_idx_ids = faiss_index.search(subset_embeddings[i:i + 1], max_query_res)
                for j in range(0, len(res_distances[0])):
                    res_d = res_distances[0][j]
                    if res_d > distance_threshold:
                        break
                    doc_id = dataset_doc_ids[res_doc_idx_ids[0][j]]
                    self.grouped_ids[type_name].add(doc_id)
                    # update the distances of a candidate doc to the closest doc in the reviewed documents
                    if doc_id not in distances[type_name] or res_d < distances[type_name][doc_id]:
                        distances[type_name][doc_id] = res_d

        # solve overlapping candidates
        print('Solve overlapping candidates...')
        for doc_id in dataset_doc_ids:
            shortest_distance = 10000
            to_remove_from_types = []
            previous_type = ''
            for type_name in distances.keys():
                if doc_id in distances[type_name] and distances[type_name][doc_id] < shortest_distance:
                    shortest_distance = distances[type_name][doc_id]
                    if previous_type != '':
                        to_remove_from_types.append(type_name)
                    previous_type = type_name

            for type_name in to_remove_from_types:
                self.grouped_ids[type_name].remove(doc_id)

        available_outscope_ids = set(dataset_doc_ids)
        # identify the documents haven't been reviewed
        print("identify the documents haven't been reviewed")
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
