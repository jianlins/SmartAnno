import logging

import sqlalchemy_dao
from sqlalchemy_dao import Dao

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Filter
from SmartAnno.gui.Workflow import Workflow
from SmartAnno.utils.AnnotationTypeDef import AnnotationTypeDef
from SmartAnno.utils.IntroStep import IntroStep
from SmartAnno.utils.KeywordsFiltering import KeywordsFiltering
from SmartAnno.utils.KeywordsUMLSExtender import KeywordsUMLSExtender
from SmartAnno.utils.KeywordsUMLSExtenderSetup import KeywordsUMLSExtenderSetup

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
wf.append(KeywordsUMLSExtenderSetup(name='umls_extender_setup'))
wf.append(KeywordsUMLSExtender(name='umls_extender', sources=ConfigReader.getValue("umls/sources"),
                               filter_by_length=ConfigReader.getValue("umls/filter_by_length"),
                               filter_by_contains=ConfigReader.getValue("umls/filter_by_contains"),
                               max_query=ConfigReader.getValue("umls/max_query")))
wf.append(
    IntroStep('<h2>Welcome to SmartAnno!</h2><h4>First, let&apos;s import txt data from a directory. </h4>',
              name='intro'))
wf.start()

wf.steps[0].complete()

with wf.dao.create_session() as session:
    records = session.query(Filter).filter(Filter.task_id == wf.task_id) \
        .filter(Filter.type_name == 'Eng')
    record = records.first()
    record.keyword = 'Eng\nEnglish'
    session.commit()

wf.steps[1].complete()
wf.steps[2].to_umls_ext_filters['Eng'].value = ('English',)
wf.steps[2].complete()
wf.steps[3].loop_workflow.steps[0].selections.value = ('Walnut Nut',)
wf.steps[3].loop_workflow.steps[0].complete()


with wf.dao.create_session() as session:
    records = session.query(Filter).filter(Filter.task_id == wf.task_id) \
        .filter(Filter.type_name == 'Eng')
    record = records.first()
    print(record.keyword)
    assert (record.keyword == 'Eng\nEnglish\nWalnut Nut')
    record.keyword = 'Eng\nEnglish'
