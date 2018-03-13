import abc

from IPython.core.display import clear_output


class Step(object):
	"""a step in a workflow"""
	global_id = -1

	def __init__(self, name=str(global_id + 1)):
		self.next_step = None
		self.previous_step = None
		self.name = name
		self.data = None
		self.workflow = None
		self.pos_id = -1
		pass

	def setPreviousStep(self, previous_step):
		self.previous_step = previous_step
		pass

	def setWorkflow(self, workflow, pos_id=None):
		self.workflow = workflow
		if pos_id is None:
			self.pos_id = len(workflow)
		pass

	def setNextStep(self, next_step):
		self.next_step = next_step
		pass

	@abc.abstractmethod
	def start(self):
		pass

	def resetParameters(self):
		self.data = None
		pass

	def goBack(self):
		clear_output(True)
		if self.previous_step is not None:
			if isinstance(self.previous_step, Step):
				self.previous_step.resetParameters()
				self.previous_step.start()
			else:
				raise TypeError(
					'Type error for ' + self.name + '\'s next_step. Only Step can be the next_step, where its next_step is ' + str(
						type(self.next_step)))
		else:
			print("previous step hasn't been set.")
		pass

	def complete(self):
		clear_output(True)
		if self.next_step is not None:
			if isinstance(self.next_step, Step):
				self.next_step.start()
			else:
				raise TypeError(
					'Type error for ' + self.name + '\'s next_step. Only Step can be the next_step, where its next_step is ' + str(
						type(self.next_step)))
		else:
			print("next step hasn't been set.")
		pass


class Workflow(object):
	"""a workflow consist a list of steps that are linked to each other. So that once one step is finished, it can trigger the next step to start."""

	def __init__(self, steps):
		self.steps = steps
		self.step_names = [None] * len(steps)
		self.name_dict = dict()
		current_step = None
		next_step = None
		for i in range(len(steps) - 1, -1, -1):
			current_step = steps[i]
			self.step_names[i] = current_step.name
			self.name_dict[current_step.name] = i
			if isinstance(current_step, type(Step)):
				raise TypeError('Type error for ' + str(
					i) + 'th steps. Only Step can be the next_step, where its next_step is ' + str(
					type(current_step)))
			current_step.setNextStep(next_step)
			current_step.setWorkflow(self)
			if i > 0:
				previous_step = steps[i - 1]
				if isinstance(previous_step, type(Step)):
					raise TypeError('Type error for ' + str(
						i - 1) + 'th steps. Only Step can be the next_step, where its next_step is ' + str(
						type(previous_step)))
				current_step.setPreviousStep(previous_step)
			next_step = current_step
		self.first_step = current_step
		pass

	def start(self):
		self.first_step.start()

	def __len__(self):
		return len(self.steps)

	def getStepById(self, step_id):
		return self.steps[step_id]

	def getStepByName(self, step_name):
		if step_name in self.name_dict and self.name_dict[step_name] < len(self.steps):
			return self.steps[self.name_dict[step_name]]
		else:
			return None

	def getDataById(self, step_id):
		step = self.getStepById(step_id)
		if step is not None:
			return step.data
		else:
			return None

	def getDataByName(self, step_name):
		step = self.getStepByName(step_name)
		if step is not None:
			return step.data
		else:
			return None
