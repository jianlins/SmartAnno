import unittest
import logging

import sqlalchemy_dao
from sqlalchemy_dao import Dao

from conf.ConfigReader import ConfigReader
from gui.PreviousNextWidgets import PreviousNextHTML
from gui.Workflow import Workflow
from utils.ReviewMLLoop import ReviewRBLoop
from utils.ReviewRBInit import ReviewRBInit


class TestReviewRB(unittest.TestCase):

    def testRBLoop(self):
        logging.getLogger().setLevel(logging.DEBUG)
        ConfigReader('conf/smartanno_conf.json')
        wf = Workflow()
        rb = ReviewRBInit(name="rb_review_init")
        wf.append(rb)
        rv = ReviewRBLoop(name='rb_review', rush_rule='../conf/rush_rules.tsv')
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
        # rb.sample_size_input.value = 3
        # rb.complete()
        # wf.start()
        # rb.sample_size_input.value = 6
        rb.navigate(rb.branch_buttons[2])
        print(rv.data['annos'])
        pass


if __name__ == '__main__':
    unittest.main()
