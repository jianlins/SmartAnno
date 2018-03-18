from gui.ForkWidgets import LoopReviews

values = ['yes', 'no', 'no', 'yes']
descriptions = ['Answer is: ', 'Answer2 is: ', 'Answer3 is: ', 'Answer4 is: ']
options = ['yes', 'no']
loop = LoopReviews(values, descriptions, options)
b = loop.loop_workflow.steps[0].branch_buttons[1]

print(hasattr(b, 'linked_step'))
