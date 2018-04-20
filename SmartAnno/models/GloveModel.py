import fileinput
from os import path
from gensim.models import KeyedVectors

from SmartAnno.gui.Workflow import logMsg

NotInitiated = 0
Initiating = 1
Initiated = 2


class GloveModel:
    glove_model = None
    status = NotInitiated

    def __init__(self, word2vec_file='models/saved/glove/glove.42B.300d.bin', vocab=1900000, vect=300):
        glove_model = None
        if GloveModel.glove_model is None and GloveModel.status == NotInitiated:
            if path.isfile(word2vec_file):
                GloveModel.status = Initiating
                logMsg('Load glove model in the backend...')
                print('Load glove model in the backend...')
                if word2vec_file.endswith('.bin'):
                    glove_model = KeyedVectors.load_word2vec_format(word2vec_file, binary=True)
                    GloveModel.status = Initiated
                else:
                    glove_model = KeyedVectors.load_word2vec_format(word2vec_file, binary=False)
                    logMsg('convert txt model to binary model...')
                    glove_model.save_word2vec_format(word2vec_file[:-3] + '.bin', binary=True)
                    GloveModel.status = Initiated
            elif path.isfile(word2vec_file[:-3] + 'txt'):
                GloveModel.status = Initiating
                logMsg('Load glove model in the backend...')
                print('Load glove model in the backend...')
                txt_model = word2vec_file[:-3] + 'txt'
                self.addDimensions(txt_model, line_to_prepend=str(vocab) + ' ' + str(vect))
                glove_model = KeyedVectors.load_word2vec_format(txt_model, binary=False)
                logMsg('convert txt model to binary model...')
                glove_model.save_word2vec_format(word2vec_file, binary=True)
                GloveModel.status = Initiated
            else:
                logMsg(("Either ", path.abspath(word2vec_file), ' or ', path.abspath(word2vec_file[:-3] + 'txt'),
                           ' exists.'))
                print(("Either ", path.abspath(word2vec_file), ' or ', path.abspath(word2vec_file[:-3] + 'txt'),
                            ' exists.'))
            GloveModel.glove_model = glove_model
        pass

    def checkModelExistance(self, word2vec_file='models/glove/glove.42B.300d.bin'):
        if path.isfile(word2vec_file) or path.isfile(word2vec_file[:-3] + 'txt'):
            return True
        else:
            return False

    def addDimensions(self, filename, line_to_prepend):
        with open(filename, 'r') as f:
            line = f.readline()
            if line.startswith(line_to_prepend):
                return
        f = fileinput.input(filename, inplace=1)
        for xline in f:
            if f.isfirstline():
                print(line_to_prepend + '\n' + xline.rstrip('\r\n'))
            else:
                print(xline.rstrip('\r\n'))
        pass
