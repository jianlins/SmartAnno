import sqlalchemy_dao
from sqlalchemy_dao import Dao

from SmartAnno.gui.DirChooser import DirChooser
from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.gui.FileIO import ReadFiles
from SmartAnno.gui.PreviousNextWidgets import PreviousNext
import glob
from SmartAnno.gui.Workflow import Workflow
from SmartAnno.utils.DBInitiater import DBInitiater
from SmartAnno.utils.DocsToDB import DocsToDB
import pandas as pd

from SmartAnno.utils.IntroStep import IntroStep

ConfigReader()
wf = Workflow([
    DBInitiater(name='db_initiator'),
    DirChooser(name='choosedir'), ReadFiles(name='readfiles'),
    DocsToDB(name='save2db')])
wf.to_continue = False

wf.getStepByName('readfiles').remove_old = True
#
# wf.getStepByName('db_initiator').need_import = True
wf.start()
wf.getStepByName('db_initiator').toggle.value = 'Yes'
wf.dao = Dao('sqlite+pysqlite:///../data/test.sqlite', sqlalchemy_dao.POOL_DISABLED)
wf.dbpath = '../data/test.sqlite'
wf.getStepByName('db_initiator').complete()
wf.getStepByName('choosedir').path = '/home/brokenjade/Documents/N2C2/smalltest/'
wf.getStepByName('choosedir')._update_files()
wf.getStepByName('choosedir').data = (wf.getStepByName('choosedir').path, wf.getStepByName('choosedir').files)
wf.getStepByName('choosedir').complete()
wf.getStepByName('readfiles').complete()
pd.set_option('display.width', 1000)
print(wf.getStepByName('readfiles').data.head(5))
# rf.data.reset_index(level=0, inplace=False)
wf.getStepByName('save2db').toggle.value = 'PyRuSh'
wf.getStepByName('save2db').complete()
