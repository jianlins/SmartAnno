from SmartAnno.gui.Main import Main

main = Main()
import logging

import sqlalchemy_dao
from sqlalchemy_dao import Dao

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.gui.Workflow import Workflow
from SmartAnno.utils.AnnotationTypeDef import AnnotationTypeDef
from SmartAnno.utils.KeywordsFiltering import KeywordsFiltering
from SmartAnno.gui.PreviousNextWidgets import PreviousNextHTML
from SmartAnno.utils.ReviewRBInit import ReviewRBInit
from SmartAnno.utils.ReviewRBLoop import ReviewRBLoop
from SmartAnno.utils.ReviewMLInit import ReviewMLInit
from SmartAnno.utils.ReviewMLLoop import ReviewMLLoop
from SmartAnno.models.logistic.LogisticBOWClassifiers import LogisticBOWClassifier
from SmartAnno.utils.DataSetChooser import DataSetChooser

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
wf.append(DataSetChooser(name='dataset_chooser', description='<h4>Choose which dateaset you want to use: </h4>'))
rb = ReviewRBInit(name="rb_review_init")
wf.append(rb)
rv = ReviewRBLoop(name='rb_review', rush_rule='../conf/rush_rules.tsv')
wf.append(rv)
wf.append(PreviousNextHTML(
    '<h2>Congratuations!</h2><h4>You have finished the initial review on the rule-base preannotations. </h4>',
    name='intro'))
wf.append(ReviewMLInit(name='ml_review_init'))
wf.append(ReviewMLLoop(name='ml_review', ml_classifier_cls=LogisticBOWClassifier))

wf.start()
wf.steps[0].complete()
wf.steps[1].complete()
wf.steps[2].toggle.value = 'n2c2_sents'
wf.steps[2].complete()
wf.steps[3].sample_size_input.value = 100

