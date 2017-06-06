from autonomic import axon, alias, help, Dendrite, Cerebellum, Synapse, Receptor

@Cerebellum
class Polling(Dendrite):

    active = []
    polled = {}


    def __init__(self, cortex):
        super(Polling, self).__init__(cortex)


    @axon
    @help("OPTIONS <start a new poll>")
    def poll(self):
        if not self.values or len(self.values) < 2:
            return 'That doesn\'t seem like a very exciting poll'

        self.active = self.values

        return 'Poll started'


    @axon
    def vote(self):
        if not self.values:
            return 'For what?'

        v = self.values[0]
        if v not in self.active:
            return 'No write-ins'

        self.polled[self.lastsender] = v
        return 'Voted'


    @axon
    def exitpoll(self):
        tally = self.polled.values()
        for item in self.active:
            self.chat('%s: %s' % (item, tally.count(item)))



