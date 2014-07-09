import inspect
from config import load_config
from id import Id
from pprint import pprint

# The core of the library methodology used
# by MongoBot. All brainmeats are Dendrites,
# inheriting the state of the cortex as the
# cortex monitors the chatroom. It also adds
# some shortcuts to cortex functions.
class Dendrite(object):

    config = None

    def __init__(self, cortex):
        self.cx = cortex

        try:
            self.config = load_config('config/%s.yaml' % type(self).__name__.lower())
        except:
            pass

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
    def butler(self):
        return self.cx.butler

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

    @property
    def settings(self):
        return self.cx.settings

    @property
    def ego(self):
        return self.cx.personality

    @property
    def mysender(self):
        return Id(self.cx.lastsender)


# This is what the cortex uses to setup the brainmeat
# libs, according to the decorators on the classes and
# functions in the lib.
def serotonin(cortex, meatname, electroshock):

    brainmeat = cortex.brainmeats[meatname]
    methods = inspect.getmembers(brainmeat)

    helps = []

    for name, method in methods:
        if not hasattr(method, 'create_command'):
            continue

        if hasattr(method, 'help') and method.help:
            me = cortex.amnesia()
            help_text = method.help.replace('%NICK%', me.nick)

            helps.append('%s%s %s' % (cortex.settings.bot.command_prefix, name, help_text))

        if hasattr(method, 'public_command'):
            cortex.public_commands.append(name)

        if name in cortex.commands and not electroshock:
            print "Warning: overwriting " + name

        cortex.commands[name] = method
        if hasattr(method, 'aliases') and method.aliases:
            for item in method.aliases:
                cortex.commands[item] = method

    if len(helps):
        if meatname in cortex.helpmenu and not electroshock:
            print "Warning: overwriting category %s in help menu" % meatname

        cortex.helpmenu[meatname] = sorted(helps)


'''
Neurons hold some vesicles. Vesicles are cool.
'''
class Neurons(object):

    cortex = None
    vesicles = {}


'''
Cerebellum is needed on any class that has methods that will be used as receptors - this is
due to pythons way of handling decorators and not binding them until the class is defined,
which is not how receptors should be utilized.

aka, this be a hack
'''
def Cerebellum(object):

    for name, method in object.__dict__.iteritems():
        if hasattr(method, 'is_receptor'):

            receptors = Neurons.vesicles.get(method.name, [])
            receptors.append({ object.__name__.lower(): method.neuron })
            Neurons.vesicles.update({ method.name: receptors })

    return object


'''
Synapse is an event emitting decorator that will fire off a neuron to all receptors that
are listening for the passed keyword.

Usage:

    @Synapse('my_keyword')
    def some_method():
        ...
'''
class Synapse(Neurons):

    def __init__(self, neuron):

        self.neuron = neuron

    def __call__(self, neuron):

        def glutamate(*args, **kwargs):

            neurotransmission = neuron(*args, **kwargs)

            vesicles = self.vesicles.get(self.neuron, [])
            for vesicle in vesicles:
                for name in vesicle:
                    if name and name in self.cortex.brainmeats:
                        vesicle[name](self.cortex.brainmeats[name], *(neurotransmission or []))

            return neurotransmission

        return glutamate


'''
Receptor is an observer decorator that will auto trigger when a neuron is fired using
a keyword the receptor is listening for.

Usage:

    @Receptor('my_keyword')
    def do_something():
        ....
'''
def Receptor(name, *args, **kwargs):

    class AutoReceptor(Neurons):

        def __init__(self, neuron, name=False):

            self.neuron = neuron
            self.name = name
            self.is_receptor = True

    def glutamate(function, *args, **kwargs):

        return AutoReceptor(function, name)

    return glutamate


# Decorators, yo

# Proposed:
# @requires(vars, connections, installs)
# @live() to run it in parietal. Iffy.
# @pipe() can pipe output to another function.
#         This is kind of just built in right
#         now.

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
# @alias(['perv', 'seriouslydude', 'gethelp'])
def alias(*args):
    def add(fn):
        fn.aliases = args
        return fn
    return add
