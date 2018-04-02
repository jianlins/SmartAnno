import spacy
from spacy.matcher import PhraseMatcher
nlp = spacy.blank('en')

color_patterns = [nlp(text) for text in ('red boat', 'green', 'yellow')]
product_patterns = [nlp(text) for text in ('boots', 'coats', 'bag')]
material_patterns = [nlp(text) for text in ('silk', 'yellow fabric')]

matcher = PhraseMatcher(nlp.vocab)
matcher.add('COLOR', None, *color_patterns)
matcher.add('PRODUCT', None, *product_patterns)
matcher.add('MATERIAL', None, *material_patterns)


doc = nlp("yellow fabric and red with red boat")
matches = matcher(doc)
for match_id, start, end in matches:
    rule_id = nlp.vocab.strings[match_id]  # get the unicode ID, i.e. 'COLOR'
    span = doc[start : end]  # get the matched slice of the doc
    print(rule_id, span.text)
