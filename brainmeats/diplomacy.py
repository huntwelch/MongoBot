from autonomic import axon, help, Dendrite

class Diplomacy(Dendrite):

    def __init__(self, cortex):
        super(Diplomacy, self).__init__(cortex)

    @axon
    @help('<get link to diplomacy board>')
    def diplomacy(self):

        link = self.config.url

        return link

