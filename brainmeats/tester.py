from autonomic import axon, alias, help, Dendrite, Cerebellum, Receptor
from pprint import pprint

@Cerebellum
class Tester(Dendrite):

    def __init__(self, cortex):
        print "INITIALIZED POOP TESTER"
        super(Tester, self).__init__(cortex)

    @axon
    @help("<idk lol>")
    @Receptor('url')
    def poop(self, *args):
        print "POOPING BACK AND FORTH FOREVER"
        for arg in args:
            pprint(arg)


        self.chat("Pooping back and forth forever")

