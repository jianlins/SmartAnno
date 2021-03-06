from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.gui.PreviousNextWidgets import PreviousNextHTML
from SmartAnno.gui.Workflow import Workflow
from SmartAnno.utils.IntroStep import IntroStep
ConfigReader('../conf/smartanno_conf2.json')
intro=IntroStep('<h2>Welcome to SmartAnno!</h2><h4>First, let&apos;s import txt data from a directory. </h4>',
							   name='intro')
wf = Workflow([intro,
					 PreviousNextHTML(name='finish',
									  description='<h3>Well done!</h3><h4>Now you have finished reviewing all the samples. ')
					 ])
wf.start()
intro.navigate(intro.branch_buttons[0])