from SmartAnno.utils.ConfigReader import ConfigReader
from SmartAnno.umls.UMLSFinder import UMLSFinder
ConfigReader()
umls = UMLSFinder(ConfigReader.getValue("api_key"), sources=[],filter_by_length=5,
                                               max_query=50,
                                               filter_by_contains=True)
print(umls.search("ketoacidosis"))