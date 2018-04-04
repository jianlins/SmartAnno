import fileinput
from os import path
from gensim.models import KeyedVectors


class GloveModel:
    glove_model = None

    def __init__(self, word2vec_file='models/saved/glove/glove.42B.300d.bin', vocab=1900000, vect=300):
        glove_model = None
        if GloveModel.glove_model is None:
            if path.isfile(word2vec_file):
                if word2vec_file.endswith('.bin'):
                    glove_model = KeyedVectors.load_word2vec_format(word2vec_file, binary=True)
                else:
                    glove_model = KeyedVectors.load_word2vec_format(word2vec_file, binary=False)
                    print('convert txt model to binary model...')
                    glove_model.save_word2vec_format(word2vec_file[:-3] + '.bin', binary=True)
            elif path.isfile(word2vec_file[:-3] + 'txt'):
                txt_model = word2vec_file[:-3] + 'txt'
                self.addDimensions(txt_model, line_to_prepend=str(vocab) + ' ' + str(vect))
                glove_model = KeyedVectors.load_word2vec_format(txt_model, binary=False)
                print('convert txt model to binary model...')
                glove_model.save_word2vec_format(word2vec_file, binary=True)
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