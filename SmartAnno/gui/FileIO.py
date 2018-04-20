from os import path

import pandas as pd
from IPython.core.display import display
from ipywidgets import widgets

from SmartAnno.gui.PreviousNextWidgets import PreviousNext
from SmartAnno.gui.Workflow import Step
import xml.etree.ElementTree as ET
from dateutil.parser import parse


class ReadFiles(PreviousNext):
    """Display a progress bar to show files (set up by DirChooser) importing process"""

    def __init__(self, name=str(Step.global_id + 1), show_previous=True, show_next=True):
        super().__init__(name, show_previous, show_next)
        self.next_button.disabled = True
        self.dataset_name = ''
        self.data = None
        self.references = None
        self.resetParameters()
        pass

    def resetParameters(self):
        self.data = pd.DataFrame(columns=['BUNCH_ID', 'DOC_NAME', 'TEXT', 'DATE', 'REF_DATE'])
        self.references = pd.DataFrame(columns=['BUNCH_ID', 'TASK_ID', 'DOC_ID', 'REVIEWED_TYPE'])
        pass

    def start(self):
        if self.previous_step.data is None:
            self.previous_step.start()
        parent_dir, files = self.previous_step.data
        label = widgets.HTML("<h4>Read files from: </h4><p>" + parent_dir + "</p>")
        progressbar = widgets.IntProgress(min=0, max=len(files), value=0, layout=widgets.Layout(width='50%'))
        rows = [label, progressbar] + self.addSeparator(top='10px') + [
            self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        display(vbox)
        for i in range(0, len(files)):
            file = files[i]
            base_name = path.basename(file)
            progressbar.value = i
            with open(parent_dir + '/' + file) as f:
                text = f.read()
                if file.lower().endswith('.xml'):
                    self.loadTextFromXml(file, text, self.data)
                else:
                    self.dataset_name = 'unknown'
                    self.data = self.data.append(pd.DataFrame([[None, base_name, text, None, None]],
                                                              columns=['BUNCH_ID', 'DOC_NAME', 'TEXT', 'DATE',
                                                                       'REF_DATE']))
        progressbar.value = progressbar.max
        self.next_button.disabled = False
        # self.data.set_index('DOC_NAME', inplace=True)
        if self.dataset_name == 'n2c2':
            self.inferRefDate(self.data)
        print("Totally " + str(len(files)) + " files have been imported into dataframe.\n"
                                             "They are parsed into "+str(len(self.data))+" records in dataframe.")

        return self.data

    def loadTextFromXml(self, file_name, content, df):
        if '<PatientMatching>' in content:
            self.dataset_name = 'n2c2'
            content = self.loadFromN2C2(file_name, content, df)
        else:
            self.dataset_name = 'i2b2'
            content = self.loadFromI2B2(file_name, content, df)
        return content

    def loadFromI2B2(self, file_name, content, df):
        '''load i2b2 dataset'''
        tree = ET.fromstring(content)
        textnodes = tree.find("TEXT")
        doc = textnodes.text.strip()
        doc_id = file_name[:-4]
        bunch_id = doc_id[:-3]
        if doc.startswith('Record date: '):
            date = parse(doc[13:doc.find('\n')].strip())
        else:
            print('document ' + doc_id + ' doesn\'t have a record date.')
            date = self.tryFindDateInTopNLines(doc)
        df.loc[len(df)] = [bunch_id, doc_id, doc, date, None]
        pass

    def loadFromN2C2(self, file_name, content, df):
        '''load n2c2 dataset'''
        tree = ET.fromstring(content)
        textnodes = tree.find("TEXT")
        text = textnodes.text.strip()
        bunch_id = file_name[:-4]
        id = 0
        for doc in text.split(
                '****************************************************************************************************'):
            doc = doc.strip()
            if len(doc.strip()) == 0:
                continue
            id += 1
            doc_id = bunch_id + '_' + str(id)
            if doc.startswith('Record date: ') or doc.startswith('Record Date: '):
                date = parse(doc[13:doc.find('\n')].strip())
            else:
                print('document ' + doc_id + ' doesn\'t have a record date.')
                date = self.tryFindDateInTopNLines(doc)
            df.loc[len(df)] = [bunch_id, doc_id, doc, date, None]
        tags = tree.find("TAGS").getchildren()
        for tag in tags:
            #     ['BUNCH_ID','TASK_ID','DOC_ID','REVIEWED_TYPE'])
            type = tag.tag.replace('-', '_').replace(' ', '_') + '_' + tag.attrib['met'].upper().replace(' ', '_')
            self.references.loc[len(self.references)] = [bunch_id, -999, None, type]
        pass

    def tryFindDateInTopNLines(self, content, n_lines=10):
        '''a few documents do not have "Record date: " in the first line, try to find a date mention in the top n lines'''
        date = None
        for line in content.split('\n')[:n_lines]:
            try:
                date = parse(line.strip())
                print('Find a date mention: ' + line + '\n\n')
                break
            except ValueError:
                pass

        return date

    def inferRefDate(self, df):
        '''find a reference date: the latest document date of a patient--according to n2c3 instruction'''
        df_grouped = df.groupby(['BUNCH_ID']).agg({'DATE': 'max'})
        df_grouped.reset_index(level=0, inplace=True)
        df_grouped = df_grouped.rename(columns={'DATE': 'REF_DATE'})
        df_grouped.head(5)
        df = df.drop(['REF_DATE'], axis=1)
        self.data = pd.merge(df, df_grouped, how='left', on='BUNCH_ID')
        pass
