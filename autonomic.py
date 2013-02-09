import inspect
from settings import CONTROL_KEY

# TODO: decorator to support command aliases

class Dendrite(object):
    def __init__(self, cortex):
        self.cx = cortex
    
    def chat(self, what):
        self.cx.chat(what)

    def announce(self, what):
        self.cx.announce(what)

    def _act(self, what, public = False, target = False):
        self.cx.act(what, public, target)

    def validate(self, what):
        self.cx.validate(what)

    def snag(self):
        self.values = self.cx.values
        self.lastsender = self.cx.lastsender
        self.context = self.cx.context
        self.members = self.cx.members


def serotonin(cortex, expansion):
    methods = inspect.getmembers(expansion)
    letter = expansion.category[:1]
    word = expansion.category[1:]

    helps = []

    for name, method in methods:
        if not hasattr(method, "create_command"):
            continue

        if hasattr(method, "help"):
            helps.append(CONTROL_KEY + name + " " + method.help)

        if name in cortex.commands:
            print "Warning: overwriting " + name

        cortex.commands[name] = method

    if len(helps):
        if letter in cortex.helpmenu:
            print "Warning: overwriting category " + letter + " in help menu"

        cortex.helpmenu[letter] = helps
        cortex.helpcategories.append("(" + letter + ")" + word)
        
def category(text):
    def add(cls):
        cls.category = text
        return cls
    return add 

def axon(fn):
    fn.create_command = True 
    return fn

def help(text):
    def add(fn):
        fn.help = text
        return fn
    return add 

