from conf.ConfigReader import ConfigReader
#
# values = ['yes', 'no', 'no', 'yes']
# descriptions = ['Answer is: ', 'Answer2 is: ', 'Answer3 is: ', 'Answer4 is: ']
# options = ['yes', 'no']
# loop = LoopReviews(values, descriptions, options)
# b = loop.loop_workflow.steps[0].branch_buttons[1]
#
# print(hasattr(b, 'linked_step'))
from umls.UMLSFinder import UMLSFinder

umls = UMLSFinder(ConfigReader().getValue('api_key'), sources=['SNOMEDCT_US'], filter_by_length=3)

print('\n'.join(umls.search('wound')))
