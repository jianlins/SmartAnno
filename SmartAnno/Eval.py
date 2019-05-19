from SmartAnno.models.svm.SVMBOWClassifier import SVMBOWClassifier
from SmartAnno.models.svm.SVMClassifier import SVMClassifier
from SmartAnno.utils.AnnotationTypeDef import AnnotationTypeDef
from SmartAnno.utils.DBInitiater import DBInitiater
from SmartAnno.utils.DataSetChooser import DataSetChooser
from SmartAnno.utils.KeywordsFiltering import KeywordsFiltering
from SmartAnno.utils.ReviewRBInit import ReviewRBInit
from SmartAnno.gui.Workflow import Workflow
from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.models.logistic.LogisticBOWClassifiers import LogisticBOWClassifiers

import logging

from SmartAnno.utils.TaskChooser import TaskChooser


def evaluate(task_name='language', classifiers=[LogisticBOWClassifiers]):
    ConfigReader()

    dbi = DBInitiater(name='db_initiator')
    tc = TaskChooser(name='tasknamer')
    dsc = DataSetChooser(name='dataset_chooser', description='<h4>Choose which dateaset you want to use: </h4>')
    anno_type = AnnotationTypeDef(
        '<h3>Annotation types:</h3><p>List all the types you want to identify below. Each type per line.<br/>If you'
        'have too many types, try set up them separately, so that you won&apos;t need to choose from a long list '
        'for each sample. </p>', name='types')
    kf = KeywordsFiltering(name='keywords')
    ri = ReviewRBInit(name="rb_review_init")
    # mi=ReviewMLInit(name='ml_review_init')
    # ml=ReviewMLLoop(name='ml_review', ml_classifier_cls=SVMBOWClassifier)
    wf = Workflow([dbi, dsc, anno_type, kf, ri
                   # ,mi,ml
                   ])
    wf.task_name = task_name
    wf.start()
    dbi.complete()
    dsc.complete()
    anno_type.complete()
    kf.complete()
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
        print("\n\nReport performance of {}:".format(cl.__name__))
        cl_instance.train(x, y)


train_size = 0.9
LogisticBOWClassifiers.train_size = train_size
SVMBOWClassifier.train_size = train_size
SVMClassifier.train_size = train_size

evaluate(task_name='language',
         classifiers=[LogisticBOWClassifiers,  SVMBOWClassifier, SVMClassifier])
