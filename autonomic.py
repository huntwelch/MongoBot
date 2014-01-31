import inspect
from settings import CONTROL_KEY


# The core of the library methodology used
# by MongoBot. All brainmeats are Dendrites,
# inheriting the state of the cortex as the
# cortex monitors the chatroom. It also adds
# some handy shortcuts to cortex functions.
class Dendrite(object):
    def __init__(self, cortex):
        self.cx = cortex

    def chat(self, what, target=False, error=False):
        self.cx.chat(what, target, error)

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
    def lastip(self):
        return self.cx.lastip

    @property
    def context(self):
        return self.cx.context

    @property
    def members(self):
        return self.cx.members


# This is what the cortex uses to setup the brainmeat
# libs, according to the decorators on the classes and
# functions in the lib.
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

        if hasattr(method, "public_command"):
            cortex.public_commands.append(name)

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


# Decorators, yo

# How the lib is stored and labelled.
# This is used internally and by the 
# help menu, so no weird characters.
def category(text):
    def add(cls):
        cls.category = text
        return cls
    return add

# Makes the function available as 
# a chat command, using the function
# name.
def axon(fn):
    fn.create_command = True
    return fn

# Makes the function available
# to non-registered users.
def public(fn):
    fn.public_command = True
    return fn

# Tell people your function is 
# there and how to use it.
def help(text):
    def add(fn):
        fn.help = text
        return fn
    return add

# Don't want to type out findfreechildpornwithukmirrors?
# @alias up 'perv'!
def alias(aliases):
    def add(fn):
        fn.aliases = aliases
        return fn
    return add
