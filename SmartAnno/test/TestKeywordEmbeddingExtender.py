import logging

import sqlalchemy_dao
from sqlalchemy_dao import Dao

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Filter
from SmartAnno.gui.Workflow import Workflow
from SmartAnno.utils.AnnotationTypeDef import AnnotationTypeDef
from SmartAnno.utils.KeywordsFiltering import KeywordsFiltering
from SmartAnno.utils.KeywordsEmbeddingExtender import KeywordsEmbeddingExtender
from SmartAnno.utils.KeywordsEmbeddingExtenderSetup import KeywordsEmbeddingExtenderSetup

logging.getLogger().setLevel(logging.DEBUG)

ConfigReader('../conf/smartanno_conf.json')

from SmartAnno.models.GloveModel import GloveModel
from threading import Thread


def prepareGloveModel():
    ConfigReader('../conf/smartanno_conf.json')
    glove_path = ConfigReader.getValue('glove/model_path')
    glove_vocab = ConfigReader.getValue('glove/vocab')
    glove_vector = ConfigReader.getValue('glove/vector')
    GloveModel(word2vec_file=glove_path, vocab=glove_vocab, vect=glove_vector)
    gm = GloveModel.glove_model


thread_gm = Thread(target=prepareGloveModel)
thread_gm.start()

wf = Workflow(config_file=ConfigReader.config_file)
wf.api_key = ConfigReader.getValue("api_key")
wf.dao = Dao('sqlite+pysqlite:///../data/test.sqlite', sqlalchemy_dao.POOL_DISABLED)
wf.task_name = 'language'
wf.append(AnnotationTypeDef(
    '<h3>Annotation types:</h3><p>List all the types you want to identify below. Each type per line.<br/>If you'
    'have too many types, try set up them separately, so that you won&apos;t need to choose from a long list '
    'for each sample. </p>', name='types'))
wf.append(KeywordsFiltering(
    name='keywords'))
wf.append(KeywordsEmbeddingExtenderSetup(name='w_e_extender_setup'))
wf.append(KeywordsEmbeddingExtender(name='w_e_extender', max_query=40))

wf.start()

wf.steps[0].complete()

with wf.dao.create_session() as session:
    records = session.query(Filter).filter(Filter.task_id == wf.task_id) \
        .filter(Filter.type_name == 'Eng')
    record = records.first()
    record.keyword = 'Eng\nEnglish'
wf.steps[1].complete()