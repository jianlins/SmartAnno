import unittest
import logging

import sqlalchemy_dao
from sqlalchemy_dao import Dao

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.gui.PreviousNextWidgets import PreviousNextHTML
from SmartAnno.gui.Workflow import Workflow
from SmartAnno.utils.ReviewMLLoop import ReviewRBLoop
from SmartAnno.utils.ReviewRBInit import ReviewRBInit


class TestReviewRB(unittest.TestCase):

    def testRBInit(self):
        logging.getLogger().setLevel(logging.WARN)

        ConfigReader()
        wf = Workflow()
        rb = ReviewRBInit(name="rb_review_init")
        wf.append(rb)
        rv = ReviewRBLoop(name='rb_review')
        wf.append(rv)
        wf.append(
            PreviousNextHTML(
                '<h2>Welcome to SmartAnno!</h2><h4>First, let&apos;s import txt data from a directory. </h4>',
                name='intro'))

        wf.filters = {'TypeA': ['heart'], 'TypeB': ['exam']}
        wf.types = ['TypeA', 'TypeB']
        wf.task_id = 1
        wf.umls_extended = {}
        wf.we_extended = {}
        wf.dao = Dao('sqlite+pysqlite:///data/demo.sqlite', sqlalchemy_dao.POOL_DISABLED)
        wf.start()
        print([doc.DOC_ID for doc in rb.data['docs']])
        print(rb.data['annos'])
        if len(rb.branch_buttons) == 0:
            # if no records in the db, the optional buttons won't show
            rb.sample_size_input.value = 3
            rb.complete()
            wf.start()
        rb.sample_size_input.value = 6
        rb.navigate(rb.branch_buttons[0])
        assert (len(rb.data['docs']) == 6)
        assert (len(rb.data['annos']) == 6)
        rb.sample_size_input.value = 5
        rb.navigate(rb.branch_buttons[1])
        assert (len(rb.data['docs']) == 11)
        assert (len(rb.data['annos']) == 11)
        print([doc.DOC_ID for doc in rb.data['docs']])
        print(rb.data['annos'])
        rb.navigate(rb.branch_buttons[2])
        assert (len(rb.data['docs']) == 11)
        assert (len(rb.data['annos']) == 11)
        print([doc.DOC_ID for doc in rb.data['docs']])
        print(rb.data['annos'])
        rb.sample_size_input.value = 7
        rb.navigate(rb.branch_buttons[0])
        assert (len(rb.data['docs']) == 7)
        assert (len(rb.data['annos']) == 7)
        print([doc.DOC_ID for doc in rb.data['docs']])
        print(rb.data['annos'])

    def testRBLoop(self):
        logging.getLogger().setLevel(logging.WARN)

        ConfigReader()
        wf = Workflow()
        rb = ReviewRBInit(name="rb_review_init")
        wf.append(rb)
        rv = ReviewRBLoop(name='rb_review')
        wf.append(rv)
        wf.append(
            PreviousNextHTML(
                '<h2>Welcome to SmartAnno!</h2><h4>First, let&apos;s import txt data from a directory. </h4>',
                name='intro'))

        wf.filters = {'TypeA': ['heart'], 'TypeB': ['exam']}
        wf.types = ['TypeA', 'TypeB']
        wf.task_id = 1
        wf.umls_extended = {}
        wf.we_extended = {}
        wf.dao = Dao('sqlite+pysqlite:///data/demo.sqlite', sqlalchemy_dao.POOL_DISABLED)
        wf.start()
        if len(rb.branch_buttons) == 0:
            # if no records in the db, the optional buttons won't show
            rb.sample_size_input.value = 3
            rb.complete()
            wf.start()
        print([doc.DOC_ID for doc in rb.data['docs']])
        print([anno.REVIEWED_TYPE for anno in wf.steps[0].data['annos'].values()])
        rb.sample_size_input.value = 1
        rb.navigate(rb.branch_buttons[1])
        pass


if __name__ == '__main__':
    unittest.main()
