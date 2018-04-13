from gui.FileIO import ReadFiles
from gui.PreviousNextWidgets import PreviousNext
import glob

rf = ReadFiles()
rf.previous_step = PreviousNext()
parent_dir = '/home/brokenjade/Documents/N2C2/train/'
files = [file[len(parent_dir):] for file in glob.glob(parent_dir + '*.xml')]
rf.previous_step.data = (parent_dir, files)
rf.start()
# print(rf.data.head(5))

print(rf.data.head(5))
