from collections import OrderedDict
from threading import Thread
from time import sleep

import spacy
from IPython.core.display import display, clear_output
from ipywidgets import widgets
from spacy.matcher import PhraseMatcher

from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.db.ORMs import Document, Annotation
from SmartAnno.gui.PreviousNextWidgets import PreviousNext
from SmartAnno.gui.Workflow import Step, logMsg
from SmartAnno.models.sampling.KeywordStratefiedSampler import KeywordStratefiedSampler

sample_options = ['Remove them', 'Keep them']
tooltips = ['Remove all previously sampled data and start a fresh sampling',
            'Keep previously sampled data and add extra sampling'
            ]


class ReviewRBInit(PreviousNext):
    """Start review samples with rule-based method in the backend.
    This is more efficient and practical when reviewed data are relatively small at the beginning."""

    description = "<h4>Review samples: </h4><p>These pre-annotations are generated by the keywords you put in. " \
                  "They will be used to train ML model in the backend.</p>"

    nlp = None
    matcher = None

    def __init__(self, description='', name=str(Step.global_id + 1), sampler_cls: type = KeywordStratefiedSampler):
        super().__init__(name=name)
        self.toggle = widgets.ToggleButtons(options=sample_options, value=sample_options[-1],
                                            description='What to do with previously sampled data? ',
                                            style=dict(description_width='initial'), button_style='info')
        self.toggle.observe(self.onPreviousSampleHandleChange)
        self.sample_size_input = widgets.BoundedIntText(value=0, min=0,
                                                        max=0, step=1,
                                                        description='Total documents you want to sample:',
                                                        style=dict(description_width='initial'))
        self.sample_size_input.observe(self.onSampleConfigChange)
        self.sampler_cls=sampler_cls
        self.sampled_summary = widgets.HTML(value='')
        self.percent_slider = widgets.IntSlider(
            value=70,
            min=0,
            max=100,
            step=5,
            description='',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d'
        )
        self.percent_slider.observe(self.onSampleConfigChange)
        # save DOC_IDs that contain or not contain keywords filters (used in sampling strategy)
        self.samples = {"contain": [], "notcontain": []}
        self.box = None
        self.data = {'docs': [], 'annos': OrderedDict()}
        self.ready = False
        # reset, continue, addmore,
        self.move_next_option = ''
        self.total = None
        self.total_contains = None
        self.un_reviewed = 0
        self.sampler = None
        self.samples = dict()
        self.current_stats = dict()
        self.max_threshold = ConfigReader.getValue("review/rb_model_threshold")
        self.sample_sizes = dict()

    def start(self):
        # print('Please wait for reading data from SmartAnno.db.', end='', flush=True)
        # self.backgroundPrinting()
        self.init_real_time()
        clear_output(True)
        self.updateBox()
        display(self.box)
        pass

    def updateBox(self):
        min_samples = 0
        recommended_samples = self.computeRecommendedSampleSize()
        title = widgets.HTML(value='<h3>Start sampling for reviewing</h3>')
        self.sample_size_input.max = self.total - len(self.data['annos'])
        self.sample_size_input.value = recommended_samples
        subtitle0 = widgets.HTML(
            value='<h4>Previously Sampled Data:</h4><p>We found <b>{}</b> previously sampled documents of this task in the database.</p>'
                .format(len(self.data['annos'])))
        subtitle1 = widgets.HTML(value='<h4>Sample size:</h4>')

        side_note = widgets.HTML(
            value='<p>If you choose <span style="background-color:  #E8E8E8">"{}"</span>, then sample size '
                  'you set below will be the amount of extra documents to be added.'.format(sample_options[1]))
        subtitle2 = widgets.HTML(
            value='<h4>Percentage to Filter: </h4><p>Choose how many percent of the documents '
                  'you want to contain the filter keywords. The rest percentage will be sampled '
                  'randomly from the documents that do not have any filter keywords.</p>')

        rows = [title]
        if len(self.data['annos']) > 0:
            rows += [subtitle0, self.toggle, side_note] + self.addSeparator(top='10px')
            # if previous samples exist, set new sample size to 0
            self.sample_size_input.value = 0
        else:
            self.toggle.value = sample_options[0]
        rows.append(subtitle1)
        rows.append(self.sample_size_input)

        self.updateSampledSummary(self.current_stats, self.sample_size_input.value,
                                  self.percent_slider.value, self.toggle.value)
        rows += self.addSeparator(top='10px') + [subtitle2, self.percent_slider] \
                + self.addSeparator(top='10px') + [self.sampled_summary] + self.addSeparator(top='10px') \
                + [self.addPreviousNext(self.show_previous, self.show_next)]
        self.box = widgets.VBox(rows)

        pass

    def computeRecommendedSampleSize(self):
        if self.total is None:
            self.total = sum(self.current_stats['all_counts'].values())
        total_not_contain = self.current_stats['all_counts']['not_contain']
        self.total_contains = self.total - total_not_contain
        recommended_samples = int(self.total_contains / 2 + total_not_contain / 4)
        if recommended_samples > 200:
            recommended_samples = 200
        return recommended_samples

    def updateSampledSummary(self, current_stats, sample_size, filter_percent, sample_option=sample_options[-1]):
        self.sample_sizes = self.sampler.getStratefiedSizes(current_stats, sample_size,
                                                            sample_option == sample_options[1],
                                                            filter_percent)
        table_html = self.renderStatsInTable(current_stats, self.sample_sizes, filter_percent)
        self.sampled_summary.value = table_html
        pass

    def init_real_time(self):
        self.data['annos'].clear()
        self.data['docs'].clear()
        self.checkPreviousReviews()
        self.initSpacyNER()
        self.queryDocIds()
        pass

    def initSpacyNER(self):
        ReviewRBInit.nlp = spacy.blank('en')
        type_phrases = dict()
        for type_name, phrases in self.workflow.filters.items():
            variations = set(phrase for phrase in phrases)
            variations.update(phrase.lower() for phrase in phrases)
            variations.update(phrase.upper() for phrase in phrases)
            variations.update(phrase[0].upper() + phrase[1:] for phrase in phrases)
            type_phrases[type_name] = ([ReviewRBInit.nlp(phrase) for phrase in variations])
            ReviewRBInit.matcher = PhraseMatcher(ReviewRBInit.nlp.vocab)
        for type_name, phrases in type_phrases.items():
            ReviewRBInit.matcher.add(type_name, None, *phrases)
        pass

    def checkPreviousReviews(self):
        """check if there is any samples have been reviewed before for the same task.
        If so, then let the user to choose how to proceed."""
        un_reviewed = 0
        with self.workflow.dao.create_session() as session:
            db_iter = session.query(Annotation, Document).join(Document, Document.DOC_ID == Annotation.DOC_ID).filter(
                Annotation.TASK_ID == self.workflow.task_id).distinct(Document.DOC_ID)
            for anno, doc in db_iter:
                self.data['annos'][anno.DOC_ID] = anno.clone()
                self.data['docs'].append(doc.clone())
                if anno.REVIEWED_TYPE is None or anno.REVIEWED_TYPE == "":
                    un_reviewed += 1

        # if len(self.data['annos']) > 0:
        #     # self.addCondition("ResetSampling", self.next_step, 'Remove previous reviewed data and restart sampling')
        #     # self.addCondition("AddExtraSampling", self.next_step, 'Keep previous reviewed data and add extra samples')
        #     self.show_next = False
        # else:
        #     self.show_next = True
        self.un_reviewed = un_reviewed
        # if un_reviewed > 0:
        #     self.addCondition("ContinueReview", self.next_step,
        #                       'Don\'t sampling, just continue to finish reviewing previous sampled data')
        pass

    def queryDocIds(self):
        self.samples = dict()
        for type_name in self.workflow.filters.keys():
            self.samples[type_name] = []

        self.sampler = self.sampler_cls(dao=self.workflow.dao,
                                                previous_sampled_ids=set(self.data['annos'].keys()),
                                                dataset_id=self.workflow.dataset_id,
                                                task_id=self.workflow.task_id)
        grouped_ids, new_ids, self.current_stats = self.sampler.getSummary(self.workflow.filters)
        print(self.current_stats)
        self.ready = True
        pass

    def renderStatsInTable(self, stats, sample_counts, percentage):
        html = []
        html.append('<h4>Summary:</h4><table  class=\'table table-striped table-bordered table-hover \'>')
        html.append('<thead>')
        html.append('<tr>')
        html.append('<th>Possible document types based on keywords</th>')
        html.append('<th>Total # of documents</th>')
        html.append('<th># of documents haven&apos;t been sampled</th>')
        html.append('<th># of documents will be sampled</th>')
        html.append('</tr>')
        html.append('</thead>')
        html.append('<tbody>')
        for type_name, all_count in stats['all_counts'].items():
            html.append('<tr>')
            html.append(
                '<td>{type_name}</td><td>{all_count}</td><td>{new_count}</td><td><b>{'
                'sample_count}</b></td> '.format(type_name=type_name, all_count=all_count,
                                                 new_count=stats['new_counts'][type_name],
                                                 sample_count=str(sample_counts[type_name])))
            html.append('</tr>')
        html.append('<tr>')
        html.append(
            '<td><b>Total</b></td><td>{all_count}</td><td>{new_count}</td><td><b>{'
            'sample_count}</b></td> '.format(all_count=self.total,
                                             new_count=sum(stats['new_counts'].values()),
                                             sample_count=sum(sample_counts.values())))
        html.append('</tr>')
        html.append('</tbody>')
        html.append('</table>')
        html.append(
            '<sup>Note: This summary is simply based on keywords search (does not take prevously reviewed true types into consideration). '
            '<br/>Each document is counted once. If one document has keywords in multiple types, this document will be counted only in the top type.</sup>')
        return ''.join(html)

    def backgroundPrinting(self):
        thread_gm = Thread(target=self.printWaiting)
        thread_gm.start()
        pass

    def printWaiting(self):
        while self.ready is False:
            print('.', end='', flush=True)
            sleep(1)
        pass

    def complete(self):
        clear_output(True)
        if self.toggle.value == sample_options[0]:
            self.restSampling()
        if sum(self.sample_sizes.values()) > 0:
            self.getSampledDocs()
        self.workflow.samples = self.data
        if self.next_step is not None:
            logMsg((self, 'workflow complete'))
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

    def restSampling(self):
        """discard previous sampling and reviewed data, start a new sampling"""
        logMsg('reset sampling')
        self.data['docs'].clear()
        self.data['annos'].clear()
        with self.workflow.dao.create_session() as session:
            anno_iter = session.query(Annotation).filter(Annotation.TASK_ID == self.workflow.task_id)
            for anno in anno_iter:
                session.delete(anno)
            session.commit()
        pass

    def getSampledDocs(self):
        self.workflow.sample_size = self.sample_size_input.value
        self.workflow.filter_percent = 0.01 * self.percent_slider.value

        # docs a list of Document object, if_contains a map with DOC_IDs as keys, 'contain' or 'notcontain' as the
        # values
        sampled_ids = self.sampler.samplingIds(self.sample_sizes,
                                               exclude_previous_sampled_id=(self.toggle.value == sample_options[-1]))

        newly_sampled_docs = self.sampler.getDocsFromSampledIds(sampled_ids, self.sample_sizes['not_contain'])
        self.data['docs'].extend(newly_sampled_docs)
        self.workflow.samples = self.data
        if len(newly_sampled_docs) > 0:
            with self.workflow.dao.create_session() as session:
                for doc in newly_sampled_docs:
                    anno = Annotation(TASK_ID=self.workflow.task_id,
                                      DOC_ID=doc.DOC_ID)
                    self.data['annos'][doc.DOC_ID] = anno.clone()

                    session.add(anno)
            session.commit()
        pass

    def onPreviousSampleHandleChange(self, change):
        if self.toggle.value == sample_options[-1]:
            # print('sample_options[-1]', self.toggle.value)
            self.sample_size_input.value = 0
            self.sample_size_input.max = self.total - len(self.data['annos'])
        else:
            # print('sample_options[0]', self.toggle.value)
            if self.sample_size_input.value == 0:
                recommended_samples = self.computeRecommendedSampleSize()
                self.sample_size_input.value = recommended_samples
            self.sample_size_input.max = self.total
        pass

    def onSampleConfigChange(self, change):
        # print(change)
        self.updateSampledSummary(self.current_stats, self.sample_size_input.value,
                                  self.percent_slider.value, self.toggle.value)
        pass
