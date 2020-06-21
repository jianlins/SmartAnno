---
layout: default
title: Configure ML Pre-annotator
nav_order: 7
---
# Configure Machine-learning-based Pre-annotator
Once some samples have been annotated, you will be asked to set some parameters as the figure below. Then, 
the machine-learning-based (ML) pre-annotator will begin running. The amount of samples need to reviewed before triggering 
ML pre-annotator can be configured by changing the value of "rb_model_threshold" in [smartanno_conf.json](https://github.com/jianlins/SmartAnno/blob/master/conf/smartanno_conf.json),
![set ml parameters](img/Selection_094.png)

These parameters are dynamically read from the ML class field, e.g. [LogisticBOWClassifier](https://github.com/jianlins/SmartAnno/blob/master/SmartAnno/models/logistic/LogisticBOWClassifier.py),
so that when we configure to use a different ML model, it's not necessary to reprogram the GUI.


