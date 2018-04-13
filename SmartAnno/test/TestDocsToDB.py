import sqlalchemy_dao
from sqlalchemy_dao import Dao

from conf.ConfigReader import ConfigReader
from gui.FileIO import ReadFiles
from gui.PreviousNextWidgets import PreviousNext
import glob
from gui.Workflow import Workflow
from utils.DocsToDB import DocsToDB
import pandas as pd

ConfigReader()
wf = Workflow()
wf.dao = Dao('sqlite+pysqlite:///data/test.sqlite', sqlalchemy_dao.POOL_DISABLED)
wf.dbpath = 'data/test.sqlite'
rf = ReadFiles()
wf.append(PreviousNext())
wf.append(rf)
parent_dir = '/home/brokenjade/Documents/N2C2/train/'
files = [file[len(parent_dir):] for file in glob.glob(parent_dir + '*.xml')]
wf.steps[0].data = (parent_dir, files)
docs2db = DocsToDB(name='save2db')
docs2db.remove_old = True
docs2db.dao = wf.dao
docs2db.dbpath = wf.dbpath
wf.append(docs2db)
rf.start()
pd.set_option('display.width', 1000)
print(rf.data.head(5))
# rf.data.reset_index(level=0, inplace=False)
docs2db.complete()