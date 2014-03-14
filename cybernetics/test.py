from autonomic import axon, alias, help, Dendrite
from synapse import Receptor

class Tester(Dendrite):

    def __init__(self, cortex):
        super(Tester, self).__init__(cortex)

    @axon
    @help("<idk lol>")
    @Receptor('linker')
    def poop(self, url=False):
        print "POOPING BACK AND FORTH FOREVER"
        self.chat("Pooping back and forth forever: %s" % url)

