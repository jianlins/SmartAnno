from conf.ConfigReader import ConfigReader
from utils.IntroStep import IntroStep
from utils.DBInitiater import DBInitiater
from gui.Workflow import Workflow

cr = ConfigReader('../conf/smartanno_conf2.json')
intro = IntroStep('<h2>Welcome to SmartAnno!</h2><h4>First, let&apos;s import txt data from a directory. </h4>',
                  name='intro')
wf = Workflow([intro,
               DBInitiater(name='db_initiater')])
wf.start()
intro.navigate(intro.branch_buttons[0])
