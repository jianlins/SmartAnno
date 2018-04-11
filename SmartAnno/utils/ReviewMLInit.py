from collections import OrderedDict

from IPython.core.display import display, clear_output
from ipywidgets import widgets

from conf.ConfigReader import ConfigReader
from gui.PreviousNextWidgets import PreviousNextWithOtherBranches
from gui.Workflow import Step, logMsg
from models.logistic.LogisticBOWClassifier import LogisticBOWClassifier


class ReviewMLInit(PreviousNextWithOtherBranches):
    """Display and allow users to set optional parameters of ML Step (class variables)"""

    description = "<h4>Review samples: </h4><p>These pre-annotations are generated by the keywords you put in. " \
                  "They will be used to train ML model in the backend.</p>"

    def __init__(self, description='', name=str(Step.global_id + 1), ml_classifier_cls=LogisticBOWClassifier):
        self.sample_size_input = None
        self.percent_slider = None
        self.samples = {"contain": [], "notcontain": []}
        self.box = None
        self.data = None
        self.docs = None
        self.annos = None
        self.reviewed = None
        self.reviewed_pos = None
        self.leftover = None
        self.ready = False
        # reset, continue, addmore,
        self.move_next_option = ''

        self.previousReviewed = OrderedDict()
        self.learning_pace = ConfigReader.getValue('review/ml_learning_pace')
        self.un_reviewed = 0
        self.parameters = dict()
        self.parameter_inputs = dict()
        self.ml_classifier_cls = ml_classifier_cls
        super().__init__(name=name)
        pass

    def start(self):
        self.init_real_time()
        self.updateBox()
        display(self.box)
        pass

    def updateBox(self):
        """ retrieve optional paramters and display them in the output cell"""
        for k in vars(self.ml_classifier_cls):
            if (not k.startswith('__')) and k != 'status' and k != 'model':
                value = getattr(self.ml_classifier_cls, k)
                self.parameters[k] = value

        rows = [widgets.HTML(value='<h3>Configure your backend machine learning model</h3>'
                                   '<p>If you are not sure what the parameters are, just leave them as they are.</p>'
                                   '<p>There are <b>' + str(
            self.leftover) + '</b> samples left unreviewed. The ML model will retrain at a pace '
                             'of once per <b>' + str(self.learning_pace) + '</b> samples.')]
        for name, value in self.parameters.items():
            if type(value) == int:
                self.parameter_inputs[name] = widgets.BoundedIntText(description=name, value=value)
                rows.append(self.parameter_inputs[name])
            elif type(value) == float:
                self.parameter_inputs[name] = widgets.BoundedFloatText(description=name, value=value)
                rows.append(self.parameter_inputs[name])
            elif type(value) == str:
                self.parameter_inputs[name] = widgets.Text(description=name, value=value)
                rows.append(self.parameter_inputs[name])

        rows += self.addSeparator(top='10px') + self.addSeparator(
            top='10px') + [self.addPreviousNext(self.show_previous, self.show_next)]
        self.box = widgets.VBox(rows)
        pass

    def init_real_time(self):
        self.readData()
        pass

    def readData(self):
        self.data = self.workflow.steps[self.pos_id - 2].data
        self.docs = self.workflow.steps[self.pos_id - 2].docs
        self.annos = self.workflow.steps[self.pos_id - 2].annos
        self.reviewed = self.workflow.steps[self.pos_id - 2].reviewed_docs
        self.reviewed_pos = len(self.reviewed)
        self.leftover = len(self.docs) - len(self.reviewed)
        pass

    def complete(self):
        clear_output(True)
        # if len(self.previousReviewed) > 0:
        #     self.continueReview()
        # else:
        #     self.addExtra()
        self.updateData()
        if self.next_step is not None:
            logMsg((self, 'ML configuration complete'))
            if isinstance(self.next_step, Step):
                if self.workflow is not None:
                    self.workflow.updateStatus(self.next_step.pos_id)
                self.next_step.start()
            else:
                raise TypeError(
                    'Type error for ' + self.name + '\'s next_step. Only Step can be the next_step, where its next_step is ' + str(
                        type(self.next_step)))
        else:
            print("next step hasn't been set.")
        pass

    def navigate(self, b):
        clear_output(True)
        # if b.description.startswith("Add"):
        #     self.move_next_option = "A"
        # elif b.description.startswith("Continue"):
        #     self.move_next_option = "C"
        # else:
        #     # else reset
        #     self.move_next_option = "R"
        self.updateData()
        if hasattr(b, 'linked_step'):
            b.linked_step.start()
        else:
            self.complete()
        pass

    def updateData(self, *args):
        """data related operations when click a button to move on to next step"""
        # if self.move_next_option == "R":
        #     self.restSampling()
        # elif self.move_next_option == "A":
        #     self.addExtra()
        # else:
        #     self.continueReview()
        for name, value in self.parameter_inputs.items():
            self.parameters[name] = value.value
            # directly change the value of class variables
            logMsg(("update settings: ", self.ml_classifier_cls, name, value.value))
            setattr(self.ml_classifier_cls, name, value.value)

        pass
