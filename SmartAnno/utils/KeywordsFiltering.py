from IPython.core.display import clear_output, display
from ipywidgets import widgets

from db.ORMs import Filter
from gui.PreviousNextWidgets import PreviousNext
from gui.Workflow import Step
from utils.TreeSet import TreeSet


class KeywordsFiltering(PreviousNext):
    """display text fields, one for each type and one extra for neutral filters (doesn't belong to any type but related to the classification task)"""
    neutral_list = 'neutral'

    def __init__(self,
                 description='<h4>Keywords Filter</h4><p>Type your keywords filter below. These key words are <b>optional</b>. They will'
                             ' be used to filter down the samples(documents or snippets) and to make starter preannotations. <br/>'
                             'You can set how much percent of the samples you want to review will be filter in <b>next step</b>. </p>'
                             '<p> This is helpful, if you estimate that '
                             'there will be too many samples with negative findings. </p>'
                             '<p>If not keywords is set, all the samples will be ask to reviewed. </p>',
                 placeholder='each phrase/word per line',
                 width='550px', height='200px', name=str(Step.global_id + 1)):
        self.text_areas = []
        self.title = widgets.HTML(value=description)
        self.filters = dict()
        self.types = []
        self.description = description
        self.placeholder = placeholder
        self.width = width
        self.height = height
        super().__init__(name)

    def start(self):
        clear_output()
        self.readDB()
        display(self.box)
        pass

    def backStart(self):
        print(self.types)
        self.updateBox()
        display(self.box)
        pass

    def readDB(self):
        self.filters.clear()
        self.types.clear()
        self.types = self.workflow.steps[self.pos_id - 1].data
        for type_name in self.types:
            if len(type_name.strip()) > 0:
                self.filters[type_name] = TreeSet()
        if self.neutral_list not in self.filters:
            self.filters[self.neutral_list] = TreeSet()
            self.types.append(self.neutral_list)

        with self.workflow.dao.create_session() as session:
            records = session.query(Filter).filter(Filter.task_id == self.workflow.task_id)
            for record in records:
                if record.type_name in self.filters:
                    self.filters[record.type_name] = TreeSet([item.strip() for item in record.keyword.split("\n") if
                                                              item.strip() != ''])
        self.updateBox()
        pass

    def updateBox(self):
        self.text_areas = [widgets.Textarea(
            value='\n'.join(self.filters[type_name]),
            placeholder=self.placeholder,
            description='"' + type_name + '" :',
            disabled=False,
            layout=widgets.Layout(width=self.width, height=self.height)) for type_name in self.types]

        rows = [self.title] + self.text_areas + self.addSeparator() + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        self.box = widgets.VBox(rows, layout=widgets.Layout(display='flex', flex_grown='column'))
        pass

    def complete(self):
        with self.workflow.dao.create_session() as session:
            # clean previous data
            session.query(Filter).filter(Filter.task_id == self.workflow.task_id).delete()
            for i in range(0, len(self.types)):
                type_name = self.types[i]
                keywords = self.text_areas[i].value.strip()
                self.filters[type_name] = TreeSet([item.strip() for item in keywords.split("\n") if
                                           item.strip() != ''])
                keywords = '\n'.join(self.filters[type_name])
                session.add(Filter(keyword=keywords, type_name=type_name, task_id=self.workflow.task_id))
        self.workflow.filters = self.filters
        super().complete()
        pass
