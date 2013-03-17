import inspect
from settings import CONTROL_KEY

# TODO: decorator to support command aliases
# TODO: standardize help description syntax


class Dendrite(object):
    def __init__(self, cortex):
        self.cx = cortex

    def chat(self, what, target=False):
        self.cx.chat(what, target)

    def announce(self, what):
        self.cx.announce(what)

    def _act(self, what, public=False, target=False):
        self.cx.act(what, public, target)

    def validate(self):
        return self.cx.validate()

    @property
    def values(self):
        return self.cx.values

    @property
    def lastsender(self):
        return self.cx.lastsender

    @property
    def context(self):
        return self.cx.context

    @property
    def members(self):
        return self.cx.members

def serotonin(cortex, expansion, electroshock):
    methods = inspect.getmembers(expansion)
    letter = expansion.category[:2]
    word = expansion.category[2:]

    helps = []

    for name, method in methods:
        if not hasattr(method, "create_command"):
            continue

        if hasattr(method, "help"):
            helps.append(CONTROL_KEY + name + " " + method.help)

        if name in cortex.commands and not electroshock:
            print "Warning: overwriting " + name

        cortex.commands[name] = method
        if hasattr(method, "aliases"):
            for item in method.aliases:
                cortex.commands[item] = method

    if len(helps):
        if letter in cortex.helpmenu and not electroshock:
            print "Warning: overwriting category " + letter + " in help menu"

        cortex.helpmenu[letter] = helps
        newcat = "(" + letter + ")" + word
        if newcat not in cortex.helpcategories:
            cortex.helpcategories.append(newcat)


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


def alias(aliases):
    def add(fn):
        fn.aliases = aliases
        return fn
    return add
