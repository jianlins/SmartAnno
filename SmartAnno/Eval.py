from models.svm.SVMBOWClassifier import SVMBOWClassifier
from utils.AnnotationTypeDef import AnnotationTypeDef
from utils.DBInitiater import DBInitiater
from utils.KeywordsFiltering import KeywordsFiltering
from utils.ReviewRBInit import ReviewRBInit
from utils.ReviewRBLoop import ReviewRBLoop
from utils.ReviewMLInit import ReviewMLInit
from utils.ReviewMLLoop import ReviewMLLoop
from gui.Workflow import Workflow
from sqlalchemy_dao import Dao
from db.ORMs import Document
from utils.IntroStep import IntroStep
from gui.PreviousNextWidgets import PreviousNextHTML
import sqlalchemy_dao
import os
from conf.ConfigReader import ConfigReader
from models.logistic.LogisticBOWClassifier import LogisticBOWClassifier

import logging


def eval(task_name='language', classifiers=[LogisticBOWClassifier]):
	ConfigReader()

	dbi = DBInitiater(name='db_initiater')
	anno_type = AnnotationTypeDef('<h3>Annotation types:</h3><p>List all the types you want to identify below. Each type per line.<br/>If you'
								  'have too many types, try set up them separately, so that you won&apos;t need to choose from a long list '
								  'for each sample. </p>', name='types')
	kf = KeywordsFiltering(name='keywords')
	ri = ReviewRBInit(name="rb_review_init")
	# mi=ReviewMLInit(name='ml_review_init')
	# ml=ReviewMLLoop(name='ml_review', ml_classifier_cls=SVMBOWClassifier)
	wf = Workflow([dbi, anno_type, kf, ri
				   # ,mi,ml
				   ])
	wf.task_name = task_name
	wf.start()
	dbi.complete()
	anno_type.complete()
	kf.complete()
	print(len(ri.branch_buttons))
	ri.complete()
	for key, value in wf.samples.items():
		print(key, len(value))
	docs = wf.samples['docs']
	annos = wf.samples['annos']
	reviewed_docs = {doc_id: anno.REVIEWED_TYPE for doc_id, anno in annos.items() if
					 anno.REVIEWED_TYPE is not None}
	x = [doc.TEXT for doc in docs[:len(reviewed_docs)]]
	y = list(reviewed_docs.values())
	print(y)
	logging.getLogger().setLevel(logging.DEBUG)
	for cl in classifiers:
		cl_instance = cl(task_name=task_name)
		cl_instance.train(x, y)


eval(classifiers=[LogisticBOWClassifier,SVMBOWClassifier])