from decimal import Decimal

import sqlalchemy_dao
from sqlalchemy import and_
from sqlalchemy_dao import Dao

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Document

cr = ConfigReader('../conf/smartanno_conf.json')
# intro = IntroStep('<h2>Welcome to SmartAnno!</h2><h4>First, let&apos;s import txt data from a directory. </h4>',
#                   name='intro')
# wf = Workflow([intro,
#                DBInitiater(name='db_initiator')])
# wf.start()
# intro.navigate(intro.branch_buttons[0])

print(18/4)
print(round(Decimal(30/4)))
print(round(0.5))

dao = Dao('sqlite+pysqlite:///../data/test.sqlite', sqlalchemy_dao.POOL_DISABLED)
with dao.create_session() as session:
    doc_iter = session.query(Document).filter(
        and_(Document.DATASET_ID == 'n2c2_sents', Document.DOC_NAME == '303_2_24')).group_by(Document.DOC_NAME)
    for doc in doc_iter:
        print(doc)
