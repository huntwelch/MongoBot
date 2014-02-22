from threading import Thread

from time import sleep
from random import randint


def something():
    x = randint(1,4)
    sleep(x)
    print 'Slept %s' % x
    

class Delegate(object):

    finished = []
    
    def __init__(self, cortex):
        return    
    
    def wrap(self, func, note):
        func()
        self.finished.append(note)

    def toss(self, func, note):
        # addlive that looks for finish
        # use lambda?
        # addlive autoremoves itself
        # reports and maybe springs a followup function
        # maybe followup is unnecessary, once threaded, can do all it needs
        thread = Thread(target=self.wrap, args=(func, note))
        thread.start()

daydream = Delegate()

for x in range(4):
    daydream.hitit(something, "Finished %s" % x)

print 'Boom'
