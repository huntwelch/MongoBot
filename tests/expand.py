from util import axon, category, help

@category("general")
class Expand:
    def __init__(self, master):
        self.master = master
        return

    @axon
    @help("stuff")
    def test(self):
        print "Attached" 
        print self
        print self.master 
        print self.master.commands 
