from autonomic import axon, alias, category, help, Dendrite
from secrete import TWIT_USER, TWIT_PASS


@category("twitter")
class Twitter(Dendrite):
    def __init__(self, cortex):
        super(Twitter, self).__init__(cortex)

    # Example command function
    @axon
    @help("<I am an example>")
    def function_name(self):
        return
