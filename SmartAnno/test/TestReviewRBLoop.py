
import logging

import sqlalchemy_dao
from sqlalchemy_dao import Dao

from conf.ConfigReader import ConfigReader
from gui.PreviousNextWidgets import PreviousNextHTML
from gui.Workflow import Workflow
from utils.ReviewRBInit import ReviewRBInit
from utils.ReviewRBLoop import ReviewRBLoop

logging.getLogger().setLevel(logging.DEBUG)

ConfigReader('../conf/smartanno_conf.json')
wf=Workflow()
rb=ReviewRBInit(name="rb_review_init")
wf.append(rb)
rv=ReviewRBLoop(name='rb_review')
wf.append(rv)
wf.append(PreviousNextHTML('<h2>Welcome to SmartAnno!</h2><h4>First, let&apos;s import txt data from a directory. </h4>',
                       name='intro'))

wf.filters={'TypeA':['heart'],'TypeB':['exam']}
wf.types=['TypeA','TypeB']
wf.task_id=1
wf.umls_extended={}
wf.we_extended={}
wf.dao=Dao('sqlite+pysqlite:///../data/demo.sqlite', sqlalchemy_dao.POOL_DISABLED)
wf.start()
rb.navigate(rb.branch_buttons[2])
rb.navigate(rb.t[2])