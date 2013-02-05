from expand import Expand
from util import serotonin

class Master:
    def __init__(self):

        self.commands = {
            "doit": self.doit,
        }

        self.expand = [
            Expand(self),
        ]

        for expansion in self.expand:
            serotonin(self, expansion)

        self.commands["test"]()

    def command(self,what):
        self.commands.get(what, self.default)()  

    def doit(self):
        print "Done"

    def default(self):
        return "Defaulted"

