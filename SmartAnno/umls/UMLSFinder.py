from __future__ import print_function

import json
import string
from collections import Set, OrderedDict

from umls.Authentication import *


class UMLSFinder:
    version = "current"
    uri = "https://uts-ws.nlm.nih.gov"
    content_endpoint = "/rest/search/" + version
    AuthClient = Authentication(ConfigReader().getValue('api_key'))
    translator = str.maketrans('', '', string.punctuation)

    def __init__(self, api_key, sources=['SNOMEDCT_US'], filter_by_length=0, max_query=50, filter_by_contains=False):
        UMLSFinder.AuthClient = Authentication(api_key)
        UMLSFinder.tgt = UMLSFinder.AuthClient.gettgt()
        self.sources = ','.join(sources)
        self.filter_by_length = filter_by_length
        self.max_query = max_query
        self.filter_by_contains = filter_by_contains
        pass

    def setSources(self, sources):
        self.sources = Set(sources)
        pass

    def search(self, input_phrase):
        pageNumber = 0
        results = OrderedDict()
        count = 0
        while True:
            ##generate a new service ticket for each page if needed
            ticket = UMLSFinder.AuthClient.getst(UMLSFinder.tgt)
            pageNumber += 1
            query = {'string': input_phrase, 'ticket': ticket, 'pageNumber': pageNumber, 'sabs': self.sources}
            r = requests.get(UMLSFinder.uri + UMLSFinder.content_endpoint, params=query)
            r.encoding = 'utf-8'
            items = json.loads(r.text)
            jsonData = items["result"]
            for result in jsonData["results"]:
                try:
                    new_phrase = result['name'].translate(UMLSFinder.translator)
                    if self.filter_by_length > 0 and len(new_phrase.split(' ')) > len(
                            input_phrase.split(' ')) + self.filter_by_length:
                        continue
                    if self.filter_by_contains and input_phrase.lower() in new_phrase.lower():
                        continue
                    if new_phrase == 'NO RESULTS':
                        break;
                    results[new_phrase.lower()] = new_phrase
                    count += 1
                    if count >= self.max_query:
                        break
                    # print(new_phrase)
                    # print(result)
                except:
                    NameError
            ##Either our search returned nothing, or we're at the end
            if jsonData["results"][0]["ui"] == "NONE":
                break
        # print('\n\n\n##################################################################')
        return list(results.values())
