import sqlalchemy_dao
from sqlalchemy_dao import Dao
from whoosh.index import create_in, open_dir
from whoosh.fields import *

from SmartAnno.db.ORMs import Document


def index():
    schema = Schema(DOC_ID=NUMERIC(stored=True), TEXT=TEXT(stored=True))
    ix = create_in("data/whoosh_idx/n2c2_sents", schema)
    writer = ix.writer()
    dao = Dao('sqlite+pysqlite:///data/test.sqlite', sqlalchemy_dao.POOL_DISABLED)
    with dao.create_session() as session:
        doc_iter = session.query(Document).filter(Document.DATASET_ID == 'n2c2_sents')
        for doc in doc_iter:
            writer.add_document(DOC_ID=doc.DOC_ID, TEXT=doc.TEXT)
        writer.commit()


def search():
    from whoosh.qparser import QueryParser
    ix = open_dir("data/whoosh_idx/n2c2_sents")
    print(ix.schema)
    ids = []
    with ix.searcher() as searcher:
        query = QueryParser("TEXT", ix.schema).parse(
            "breath OR (heart AND failure)")
        results = searcher.search(query, limit=10000, terms=True)
        for res in results:
            print(res['DOC_ID'])
            print(res.matched_terms())
            ids.append(res['DOC_ID'])
    # dao = Dao('sqlite+pysqlite:///data/test.sqlite', sqlalchemy_dao.POOL_DISABLED)
    # with dao.create_session() as session:
    #     for id in ids:
    #         doc = session.query(Document).filter(Document.DOC_NAME == id).first()
    #         print(id, doc.TEXT)
    # print(len(ids))


index()
# search()


# from whoosh.index import create_in
# from whoosh.fields import *
# schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
# ix = create_in("data/tmp", schema)
# writer = ix.writer()
# writer.add_document(title=u"First document", path=u"/a",
#                    content=u"This is the first document we've added!")
# writer.add_document(title=u"Second document", path=u"/b",
#                    content=u"The second one is even more interesting!")
# writer.commit()
# from whoosh.qparser import QueryParser
# with ix.searcher() as searcher:
#    query = QueryParser("content", ix.schema).parse("first")
#    results = searcher.search(query)
#    print(results[0])
