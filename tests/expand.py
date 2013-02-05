from util import axion

class Expand:
    def __init__(self, master):
        self.master = master
        return

    @axion
    def test(self):
        print "Attached" 
        print self
        print self.master 
        print self.master.commands 
