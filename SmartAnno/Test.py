from conf.ConfigReader import ConfigReader
ConfigReader()
ConfigReader.setValue("glove/vocab", 300)
ConfigReader.setValue("glove/vector",190000)
ConfigReader.setValue("glove/path", 'models/saved/glove/glove.42B.300d.bin')
print(ConfigReader().configurations)