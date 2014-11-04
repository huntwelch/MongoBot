from autonomic import axon, alias, help, Dendrite, Cerebellum, Synapse, Receptor

@Cerebellum
class Civics(Dendrite):

    # https://www.govtrack.us/developers/api
    # http://votesmart.org/share/api#.VFlbrvTF-sg
    # http://sunlightlabs.github.io/openstates-api/

    def __init__(self, cortex):
        super(Civics, self).__init__(cortex)


    @axon
    @help("<I am an example>")
    def function_name(self):
        return

