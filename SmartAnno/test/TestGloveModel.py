from models.GloveModel import GloveModel
from  conf.ConfigReader import ConfigReader
ConfigReader('../conf/smartanno_conf.json')
glove_path = ConfigReader.getValue('glove/model_path')
glove_vocab = ConfigReader.getValue('glove/vocab')
glove_vector = ConfigReader.getValue('glove/vector')
