import re
import string
from os import path
import gensim
import nltk
import numpy as np
import spacy
from PyRuSH.RuSH import RuSH
from gensim.corpora import Dictionary
from gensim.models import KeyedVectors
import spacy.matcher as matcher


class PreProcessing:
    def __init__(self,
                 annotation_type='SOCIAL_SUPPORT',
                 default_value='no mention',
                 filter_file='conf/keywords_filter.txt',
                 stopwords_file='conf/stop_words.txt',
                 word2vec_file='models/glove.word2vec.txt.bin',
                 rush_rules='conf/rush_rules.tsv',
                 max_token_per_sentence=150):
        # each time we only train/predict a models for one annotation type
        # set an arbitrary max length of sentences, so that we can pad sentences without knowing the max length of sentences in testing set.

        self.max_token_per_sentence = max_token_per_sentence
        self.annotation_type = annotation_type
        self.default_value = default_value
        self.real_max_length = 0
        self.rush = RuSH(rush_rules)
        self.html_tokens_p = re.compile('^\&[a-z]{2,4}\;$')
        self.punctuations = set(string.punctuation)
        # keep '?'
        self.punctuations.remove('?')
        self.spacy_nlp = spacy.load('en', disable=['parser', 'tagger', 'ner'])
        self.matcher = None
        self.corpus = None
        keywords_filter = []
        print('load filter keywords')
        # load filter keywords
        if path.isfile(filter_file):
            f = open(filter_file, 'r')
            keywords_filter = [line for line in f.readlines() if not line.startswith('#')]
            f.close()
        if len(keywords_filter) > 0:
            self.matcher = matcher.PhraseMatcher(self.spacy_nlp.tokenizer.vocab, max_length=6)
            for keyword in keywords_filter:
                self.matcher.add(keyword, None)

        print('load stopwords')
        # load stop words
        if path.isfile(stopwords_file):
            f = open(stopwords_file, 'r')
            self.my_stopwords = set(f.readlines())
            f.close()
        else:
            self.my_stopwords = set(nltk.corpus.stopwords.words('english'))
            f = open(stopwords_file, 'w')
            f.writelines('\n'.join(self.my_stopwords))
            f.close()

        print('load label dictionary')
        self.label_dict = None
        self.label_dict_file = 'models/' + self.annotation_type + '_labels.dict'
        # load dictionary
        if path.isfile(self.label_dict_file):
            self.label_dict = Dictionary.load(self.label_dict_file)

        print('load glove model')
        # self.glove_model = glove2word2vec.smart_open(word2vec_file)
        if path.isfile(word2vec_file):
            if word2vec_file.endswith('.bin'):
                self.glove_model = KeyedVectors.load_word2vec_format(word2vec_file, binary=True)
            else:
                self.glove_model = KeyedVectors.load_word2vec_format(word2vec_file, binary=False)
                print('convert txt model to binary model...')
                self.glove_model.save_word2vec_format(word2vec_file + '.bin', binary=True)

        pass

    """ Given a plain text document, return a list of tokenized sentences that contain filter keywords"""

    def processDocument(self, doc_text, tokenized_sentences=[], labels=[], annotations=None, doc_id=None):
        print(doc_id)
        sentences = self.rush.segToSentenceSpans(doc_text)
        sentences_txt = ([doc_text[sentence.begin:sentence.end] for sentence in sentences])
        anno_id = 0
        for i in range(0, len(sentences_txt)):
            sentence = sentences_txt[i]
            label = self.default_value
            # if annotations are available, read as labels
            if annotations is not None:
                if len(annotations) > 0:
                    if anno_id < len(annotations) \
                            and annotations[anno_id]['start'] >= sentences[i].begin \
                            and annotations[anno_id]['end'] <= sentences[i].end:
                        label = list(annotations[anno_id]['attributes'].values())[0]
                        anno_id += 1
                    elif anno_id < len(annotations) \
                            and annotations[anno_id]['end'] <= sentences[i].begin:
                        print(doc_id + str(annotations[anno_id]) + 'was skipped')
                        i -= 1
                        anno_id += 1

            words = [token for token in self.spacy_nlp.make_doc(sentence)
                     if len(''.join(ch for ch in token.text if ch not in self.punctuations)) > 0
                     and not self.html_tokens_p.search(token.text)
                     and not token.text.replace('.', '', 1).isdigit()
                     and not token.text.replace('-', '', 1).isdigit()
                     and token.text not in self.my_stopwords]
            if self.real_max_length < len(words):
                self.real_max_length = len(words)
            if self.get_matches(words):
                if len(words) < self.max_token_per_sentence:
                    tokenized_sentences.append(self.pad_sentence([word.text for word in words]))
                    labels.append(label)
                else:
                    begin = 0
                    words = [word.text for word in words]
                    while begin <= len(words) - self.max_token_per_sentence:
                        tokenized_sentences.append(words[begin:self.max_token_per_sentence])
                        # overlap the sliced sub-sentences
                        begin += int(self.max_token_per_sentence / 2)
                    if begin < len(words):
                        tokenized_sentences.append(self.pad_sentence(words[len(words) - self.max_token_per_sentence:]))

        return tokenized_sentences

    def get_matches(self, sentence_tokens):
        if self.matcher is None:
            return True
        matches = self.matcher(sentence_tokens)
        for ent_id, start, end in matches:
            yield (ent_id, start, end)

    # def processLabelledCorpus(self, corpus_dir):
    #     corpus_reader = EhostCorpusReader(corpus_dir)
    #     corpus = corpus_reader.parse()
    #     self.corpus = corpus
    #     tokenized_sentences = []
    #     labels = []
    #     for doc_id, doc in corpus.items():
    #         if self.annotation_type in doc['categorized']:
    #             annotations = [doc['annotations'][anno_id] for anno_id in doc['categorized'][self.annotation_type]]
    #         else:
    #             annotations = []
    #         self.processDocument(doc['text'], tokenized_sentences, labels, annotations, doc_id)
    #
    #     x, y = self.vectorize(tokenized_sentences, labels)
    #     return x, y

    def pad_sentence(self, sentence, padding_word="<PAD/>"):
        """
        Revised from alexander-rakhlin's code
        Pads all sentences to the same length. The length is defined by the longest sentence.
        Returns padded sentences.
        """
        num_padding = self.max_token_per_sentence - len(sentence)
        new_sentence = sentence + [padding_word] * num_padding
        return new_sentence

    def vectorize(self, sentences, labels=[]):
        """
        Revised from alexander-rakhlin's code, use glove models instead.
        Maps sentencs and labels to vectors based on a vocabulary.
        """

        print(labels)
        if self.label_dict is None:
            self.label_dict = gensim.corpora.Dictionary([set(labels)])
            self.label_dict.compactify()
            self.label_dict.save(self.label_dict_file)
            self.label_dict.save_as_text(self.label_dict_file + '.txt')

        print(set(labels))
        x = np.array([[self.glove_model.word_vec(word) if word in self.glove_model.vocab
                       else np.random.uniform(-0.25, 0.25, self.glove_model.vector_size) for word in sentence] for
                      sentence in sentences])
        y = None
        if len(labels) > 0:
            y = np.zeros((len(labels), len(self.label_dict.keys())))
            for i in range(0, len(labels)):
                label = labels[i]
                y[i][self.label_dict.token2id[label]] = 1

            shuffle_indices = np.random.permutation(np.arange(len(y)))
            x = x[shuffle_indices]
            y = y[shuffle_indices]
        return x, y
