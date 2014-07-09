from autonomic import axon, help, Dendrite

# MongoBot itself actually has a facebook page
# which I think just reposts from twitter, since
# he tweets but doesn't really fb. Though he could...
class Facebook(Dendrite):
    def __init__(self, cortex):
        super(Facebook, self).__init__(cortex)

    @axon
    @help('<show link to %NICK%\'s community page>')
    def fblink(self):

        return self.config.page

