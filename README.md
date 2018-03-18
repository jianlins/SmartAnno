# SmartAnno

SmartAnno is a semi-automatic annotation tool implemented within jupyter notebook. It use deep learning model in the backend to learn a smart model over time while users annotating the data. It also integrate word embedding, and UMLS synonym heuristics to improve learning rate.



## Installation

```bash
pip install smartanno
```

## How to use

Within jupyter notebook, add a python cell, type: 
```python
from gui.GUI import GUI
gui=GUI()
```
Then, create another python cell, type:
```python
gui.start()
```
Execute these two cells.
