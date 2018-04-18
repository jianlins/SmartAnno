from db.ORMs import Annotation, Document
from models.sampling.KeywordStratefiedSampler import KeywordStratefiedSampler
import logging

import sqlalchemy_dao
from sqlalchemy_dao import Dao

from conf.ConfigReader import ConfigReader
from gui.PreviousNextWidgets import PreviousNextHTML
from gui.Workflow import Workflow
from models.logistic.LogisticBOWClassifier import LogisticBOWClassifier
from utils.AnnotationTypeDef import AnnotationTypeDef
from utils.DataSetChooser import DataSetChooser
from utils.KeywordsFiltering import KeywordsFiltering
from utils.ReviewMLInit import ReviewMLInit
from utils.ReviewMLLoop import ReviewMLLoop
from utils.ReviewRBInit import ReviewRBInit
from utils.ReviewRBLoop import ReviewRBLoop

logging.getLogger().setLevel(logging.DEBUG)

ConfigReader('../conf/smartanno_conf.json')

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
wf.append(DataSetChooser(name='dataset_chooser'))
wf.append(PreviousNextHTML(
    '<h2>Congratuations!</h2><h4>You have finished the initial review on the rule-base preannotations. </h4>',
    name='intro'))
wf.start()
wf.steps[0].complete()
wf.steps[1].complete()
wf.steps[2].toggle.value = 'n2c2_sents'
wf.steps[2].complete()
data = {'annos': dict(), 'docs': []}
with wf.dao.create_session() as session:
    db_iter = session.query(Annotation, Document).join(Document, Document.DOC_ID == Annotation.DOC_ID).filter(
        Annotation.TASK_ID == wf.task_id).distinct(Document.DOC_ID)
    for anno, doc in db_iter:
        data['annos'][doc.DOC_ID] = anno.clone()
        data['docs'].append(doc.clone())

sampler = KeywordStratefiedSampler(dao=wf.dao,
                                   previous_sampled_ids=set(data['annos'].keys()), dataset_id=wf.dataset_id)
print(data['annos'].keys())
grouped_ids, new_ids, stats = sampler.getSummary(wf.filters)
print('\n'.join(str(ele) for ele in stats.items()))
sampled = sampler.sampling(130000, grouped_ids, new_ids,exclude_previous_sampled_id=True)
# for docs in sampled:
#     print(docs.DOC_NAME)
print(len(sampled))
