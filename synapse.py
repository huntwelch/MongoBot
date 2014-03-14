from autonomic import Dendrite
from pprint import pprint

'''
Neurons hold some vesicles. Vesicles are cool.
'''
class Neurons(object):

    vesicles = dict()


'''
Cerebellum is needed on any class that has methods that will be used as receptors - this is
due to pythons way of handling decorators and not binding them until the class is defined,
which is not how receptors should be utilized.

aka, this be a hack
'''
def Cerebellum(object):

    for name, method in object.__dict__.iteritems():
        if hasattr(method, 'is_receptor'):
            Neurons.vesicles.update({ method.name: [ Dendrite(object), method.neuron ]})

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

            vesicle, cell = self.vesicles.get(self.neuron, [])
            if vesicle:
                cell(vesicle, *(neurotransmission or []))

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
            print neuron

            self.neuron = neuron
            self.name = name
            self.is_receptor = True

    def glutamate(function, *args, **kwargs):

        return AutoReceptor(function, name)

    return glutamate

