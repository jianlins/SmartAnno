import time
from threading import Thread

li = [1, 2, 3, 4]



def printer():
    for m in range(0, 100):
        time.sleep(1.2)
        print(len(li))


thread_gm = Thread(target=printer)
thread_gm.start()
for i in range(1, 100):
    li.append(i)
    time.sleep(1)
