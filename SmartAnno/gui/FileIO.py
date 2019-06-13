import random
from os import path

import pandas as pd
from IPython.core.display import display, clear_output
from ipywidgets import widgets, Button

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
        self.start_import_btn = Button(description="Start Import")
        self.progressbar = widgets.IntProgress(min=0, max=1, value=0, layout=widgets.Layout(width='50%'))
        self.sample_num = widgets.Text(
            value='',
            placeholder='',
            description='Number of files to sample',
            disabled=False, style={'description_width': 'initial'}
        )
        pass

    def resetParameters(self):
        self.data = pd.DataFrame(columns=['BUNCH_ID', 'DOC_NAME', 'TEXT', 'DATE', 'REF_DATE'])
        self.references = pd.DataFrame(columns=['BUNCH_ID', 'TASK_ID', 'DOC_ID', 'REVIEWED_TYPE'])
        pass

    def start(self):
        def startImport(b):
            b.disabled = True
            print('start import...')
            parent_dir, files = self.previous_step.data
            self.progressbar.max = int(self.sample_num.value)
            if not parent_dir.lower().endswith('.zip'):
                sampled_ids = random.sample(range(0, len(files)), self.progressbar.max)
                for i in range(0, self.progressbar.max):
                    file = files[sampled_ids[i]]
                    base_name = path.basename(file)
                    self.progressbar.value = i
                    with open(parent_dir + '/' + file) as f:
                        text = f.read()
                        if file.lower().endswith('.xml'):
                            self.loadTextFromXml(file, text, self.data)
                        else:
                            self.dataset_name = 'unknown'
                            self.data = self.data.append(pd.DataFrame([[None, base_name, text, None, None]],
                                                                      columns=['BUNCH_ID', 'DOC_NAME', 'TEXT', 'DATE',
                                                                               'REF_DATE']))
                self.progressbar.value = self.progressbar.max
            else:
                sampled_ids = random.sample(range(0, len(self.file_list)), self.progressbar.max)
                for i in range(0, self.progressbar.max):
                    finfo = self.file_list[sampled_ids[i]]
                    ifile = self.zfile.open(finfo)
                    doc_text = ifile.read().decode("utf-8")
                    base_name = path.basename(finfo.filename)
                    self.progressbar.value = i
                    if finfo.filename.lower().endswith('.xml'):
                        self.loadTextFromXml(finfo, doc_text, self.data)
                    else:
                        self.dataset_name = 'unknown'
                        self.data = self.data.append(pd.DataFrame([[None, base_name, doc_text, None, None]],
                                                                  columns=['BUNCH_ID', 'DOC_NAME', 'TEXT', 'DATE',
                                                                           'REF_DATE']))
                self.zfile.close()
                self.progressbar.value = self.progressbar.max
            self.next_button.disabled = False
            # self.data.set_index('DOC_NAME', inplace=True)
            if self.dataset_name == 'n2c2':
                self.inferRefDate(self.data)
            print("Totally " + str(len(sampled_ids)) + " files have been imported into dataframe.\n"
                                                 "They are parsed into " + str(len(self.data)) + " records in dataframe.")
            pass

        if self.previous_step.data is None:
            self.previous_step.start()
        parent_dir, files = self.previous_step.data
        if not parent_dir.lower().endswith('.zip'):
            label = widgets.HTML("<h4>Read %s files from: </h4><p>%s</p>".format(len(files), parent_dir))
            self.start_import_btn.on_click(startImport)
            self.sample_num.value = str(len(files))
            self.progressbar.max = len(files)
            rows = [label, self.sample_num, self.start_import_btn, self.progressbar] + self.addSeparator(top='10px') + [
                self.addPreviousNext(self.show_previous, self.show_next)]
        else:
            import zipfile, os
            parent_dir = os.path.join(self.previous_step.path, parent_dir)
            self.zfile = zipfile.ZipFile(parent_dir)
            print('reading file list from {} ...'.format(parent_dir))
            self.file_list = [f for f in self.zfile.infolist() if not f.is_dir()]
            label = widgets.HTML("<h4>Read {} files from: </h4><p>{}</p>".format(len(self.file_list), parent_dir))
            self.sample_num.value = str(len(self.file_list))
            self.progressbar.max = len(self.file_list)
            self.start_import_btn.on_click(startImport)
            rows = [label, self.sample_num, self.start_import_btn, self.progressbar] + self.addSeparator(top='10px') + [
                self.addPreviousNext(self.show_previous, self.show_next)]
        vbox = widgets.VBox(rows)
        vbox.layout.flex_grown = 'column'
        clear_output()
        display(vbox)
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
