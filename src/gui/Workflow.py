import abc


class Step(object):
	"""a step in a workflow"""

	def __init__(self):
		self.next_step = None
		self.previous_step = None
		self.name = ''
		self.data = None
		self.workflow = None
		pass

	def setPreviousStep(self, previous_step):
		self.previous_step = previous_step
		pass

	def setWorkflow(self, workflow):
		self.workflow = workflow
		pass

	def setNextStep(self, next_step):
		self.next_step = next_step
		pass

	@abc.abstractmethod
	def start(self):
		pass

	def resetParameters(self):
		self.data = None
		self.workflow = None
		pass

	def complete(self):
		if self.workflow is not None:
			self.workflow.data.append(self.data)
		if self.next_step is not None:
			if isinstance(self.next_step, Step):
				self.next_step.start()
			else:
				raise TypeError('Type error for ' + self.name + '\'s next_step. Only Step can be the next_step, where its next_step is ' + str(
					type(self.next_step)))
		else:
			print("next step hasn't been set.")
		pass

	def goBack(self):
		if self.previous_step is not None:
			if isinstance(self.previous_step, Step):
				self.previous_step.start()
			else:
				raise TypeError('Type error for ' + self.name + '\'s next_step. Only Step can be the next_step, where its next_step is ' + str(
					type(self.next_step)))
		else:
			print("previous step hasn't been set.")
		pass


class SubStep(object):
	"""a substep within a step, the transition is implemented through call self.next_step (a function)"""

	def __init__(self):
		self.next_step = None
		self.next_steps = []
		self.options = []
		self.previous_step = None
		self.name = ''
		self.value = None
		pass

	def setPreviousStep(self, previous_step):
		self.previous_step = previous_step
		pass

	def setNextStep(self, next_step):
		self.next_step = next_step
		pass

	def setOpitionalNextSteps(self, next_steps):
		if len(self.next_steps) != len(self.options):
			raise ValueError('If you use OpitionalNextSteps which next step is depended on the current substep value, you need make sure '
							 + '"self.next_steps" and "self.options" have the same size. However, current len(self.options)=' + str(len(self.options))
							 + ', and len(self.next_steps)=' + str(len(self.next_steps)))
		for i in range(0, len(self.options)):
			self.next_steps[self.options[i]] = next_steps[i]
		pass

	@abc.abstractmethod
	def start(self):
		pass

	def resetParameters(self):
		self.value = None
		pass

	def previous_step(self):
		self.previous_step()
		pass

	def complete(self):
		if self.next_step is not None:
			self.next_step()
		elif len(self.next_steps) > 0:
			if self.value in self.next_steps:
				self.next_steps[self.value]()
			else:
				raise ValueError("Current substep value: " + str(self.value) + " hasn't been associated with a next_step function.")
		pass


class Workflow(object):
	"""a workflow consist a list of steps that are linked to each other. So that once one step is finished, it can trigger the next step to start."""

	def __init__(self, steps):
		self.data = []
		current_step = None
		next_step = None
		for i in range(len(steps) - 1, -1, -1):
			current_step = steps[i]
			if isinstance(current_step, type(Step)):
				raise TypeError('Type error for ' + str(i) + 'th steps. Only Step can be the next_step, where its next_step is ' + str(
					type(current_step)))
			current_step.setNextStep(next_step)
			current_step.setWorkflow(self)
			if i > 0:
				previous_step = steps[i - 1]
				if isinstance(previous_step, type(Step)):
					raise TypeError('Type error for ' + str(i - 1) + 'th steps. Only Step can be the next_step, where its next_step is ' + str(
						type(previous_step)))
				current_step.setPreviousStep(previous_step)
			next_step = current_step
		self.first_step = current_step
		pass

	def start(self):
		self.first_step.start()
