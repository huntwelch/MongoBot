from __future__ import print_function
import inspect
import sys

from config import load_config
from id import Id
from pprint import pprint


# The core of the library methodology used
# by MongoBot. All brainmeats are Dendrites,
# inheriting the state of the cortex as the
# cortex monitors the chatroom. It also adds
# some shortcuts to cortex functions.

# future experiment

def router(self):
    destination = self.values.pop(0)
    if not self[destination].create_command: return
    return self[destination]()

def autocommand(fn_name):
    def add(object):
        object.routed = True
        object[fn_name] = router
        return object

    return add


class Dendrite(object):

    config = None
    secrets = None

    def __init__(self, cortex):
        self.cx = cortex
        name = type(self).__name__.lower()

        # Load in brainmeats specific secrets and only make those available as first
        # class secrets to the brainmeats
        if name in self.cx.secrets:
            self.secrets = self.cx.secrets[name]

        # Load in config file by the same name as the brainmeats, if available
        try:
            self.config = load_config('config/%s.yaml' % name)
        except Exception as e:
            print(e)
            pass

    def chat(self, what, target=False, error=False):
        self.cx.chat(what, target, error)

    def debug(self, what, target=False):
        self.cx.debug(what, target)

    def announce(self, what, channel=None):
        self.cx.announce(what, channel)

    def _act(self, what, public=False, target=False):
        self.cx.act(what, public, target)

    def validate(self):
        return self.cx.validate()

    @property
    def botname(self):
        return self.cx.thalamus.name

    @property
    def values(self):
        return self.cx.values

    @property
    def flags(self):
        return self.cx.flags

    @property
    def butler(self):
        return self.cx.butler

    @property
    def lastsender(self):
        return self.cx.lastsender

    @property
    def lastid(self):
        return self.cx.lastid

    @property
    def lastip(self):
        return self.cx.lastip

    @property
    def context(self):
        return self.cx.context

    @property
    def context_is_channel(self):
        return self.cx.context.startswith('#')

    @property
    def members(self):
        return self.cx.members

    @property
    def settings(self):
        return self.cx.settings

    @property
    def ego(self):
        return self.cx.personality

    # @property
    # def mysender(self):
    #    return Id(self.cx.lastsender)


# This is what the cortex uses to setup the brainmeat
# libs, according to the decorators on the classes and
# functions in the lib.
def serotonin(cortex, meatname, electroshock):

    brainmeat = cortex.brainmeats[meatname]
    methods = inspect.getmembers(brainmeat)

    helps = []

    if hasattr(brainmeat, 'routed'):
        cortex.commands[meatname] = brainmeat[meatname]
        return


    for name, method in methods:
        if not hasattr(method, 'create_command'):
            continue

        if hasattr(method, 'help') and method.help:
            me = cortex.amnesia()
            help_text = method.help.replace('%NICK%', me.nick)

            helps.append('%s%s %s' % (cortex.settings.bot.command_prefix, name, help_text))
        else:
            helps.append('%s%s (undocumented)' % (cortex.settings.bot.command_prefix, name))


        if hasattr(method, 'public_command'):
            cortex.public_commands.append(name)

        if name in cortex.commands and not electroshock:
            print("Warning: overwriting %s command" % name)

        cortex.commands[name] = method
        if hasattr(method, 'aliases') and method.aliases:
            for item in method.aliases:
                cortex.commands[item] = method

    cortex.helpmenu[meatname] = ['No commands for this meat.']

    if len(helps):
        cortex.helpmenu[meatname] = sorted(helps)

    helpfile = open('helpfiles/%s' % meatname, 'w')
    for item in sorted(helps):
        helpfile.write("%s\n" % item)


# Neurons hold some vesicles. Vesicles are cool.
class Neurons(object):

    cortex = None
    vesicles = {}


# Cerebellum is needed on any class that has
# methods that will be used as receptors - this is
# due to pythons way of handling decorators and
# not binding them until the class is defined,
# which is not how receptors should be utilized.
#
# aka, this be a hack
def Cerebellum(object):

    for name, method in object.__dict__.iteritems():
        if hasattr(method, 'is_receptor'):

            receptors = Neurons.vesicles.get(method.name, [])
            receptors.append({object.__name__.lower(): method.neuron})
            Neurons.vesicles.update({method.name: receptors})

    return object


# Synapse is an event emitting decorator that will
# fire off a neuron to all receptors that are
# listening for the passed keyword.
#
# Usage:
#
#     @Synapse('my_keyword')
#     def some_method():
#         ...
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


# Receptor is an observer decorator that will
# auto trigger when a neuron is fired using
# a keyword the receptor is listening for.
#
# Usage:
#
#     @Receptor('my_keyword')
#     def do_something():
#         ....
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


