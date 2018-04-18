from conf.ConfigReader import ConfigReader
from models.rulebased.RBDocumentClassifier import RBDocumentClassifierFactory
ConfigReader()
filters={'TypeA': ['patient'], 'TypeB': ['family'], 'Irrelevant': []}
rb_classifier = RBDocumentClassifierFactory.genDocumentClassifier(filters)
print(rb_classifier.classify('The  Patient is ok'))


txt='''Record date: 2126-11-07\n\n\n\n\tCARDIOLOGY\n\n\t\n\n\tFAMILY HEALTH CLINIC\n\n\t\n\n\n\n\tInterval History:\n\n   Dr. Devan Chandler\n\n100 CRP\n\n\n\nRE:  Bruce Corona\n\nFHC Unit #:  795-76-17\n\n\n\nDear Dunham:\n\n\n\nI had the pleasure of seeing  Bruce Corona in the Cardiology Department office for a f/u visit.  Since I last saw him, he continues to complain of dyspnea.  An ETT was negative for ischemia.  PFTs were not really useful.  CT of the chest showed scarring/fibrosis.  His NT-proBNP has been on the marginal side, though he is without evidence for overt CHF.\n\n\n\nMedications:  Aspirin 325 mg qd, Flomax 0.4 mg qd, Lopressor 25 mg bid, Lipitor 10 mg qd, Lisinopril 20 mg qd, Colace 100 mg tid.\n\n\n\nPhysical examination:  Reveals him to be well appearing. His BP is 120/70 and his heart rate is 60 and regular. He is 170 pounds.  There is no jugular venous distention and carotid pulses are 2+ bilaterally without bruits.  His lungs are clear throughout, and notably demonstrate only very slight dullness at the left base.  His sternotomy is healing well and is stable.  His apical impulse is non-displaced with a slightly irregular rate and rhythm, a normal S1 and S2.  He has an S3 gallop.  No murmur.  His abdomen is benign without hepatosplenomegaly, bruits, or a dilated aorta.  There is no pedal edema and posterior tibial pulses are 2+ bilaterally.\n\n\n\nEKG:  NSR with a 1st degree AV block.  He has a LBBB, which is chronic.\n\n\n\nImpression:\n\n\n\n1.CAD, s/p MI: currently stable.\n\n\n\n2. Hypertension: under good control.\n\n\n\n3.Hypercholesterolemia: controlled\n\n\n\n4. Dyspnea: I suspect he has an element of diastolic dysfunction.  I will restart low-dose lasix.\n\n\n\nThank you very much for the opportunity to participate in his care.\n\n\n\nWith best regards,\n\n\n\nBruce D. Brian, Jr., M.D.\n\n\n\n\tSigned electronically by   Bruce D Brian MD  on  Nov 7, 2126'''
print(rb_classifier.classify(txt))