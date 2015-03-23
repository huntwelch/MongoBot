from autonomic import axon, alias, help, Dendrite, Cerebellum, Synapse, Receptor

@Cerebellum
class Dice(Dendrite):

    players = {}

    def __init__(self, cortex):
        super(Dice, self).__init__(cortex)


    # Example command function
    # The axon decorator adds it to the available chatroom commands,
    # based on the name of the function. The @help adds an entry to
    # the appropriate category.
    @axon
    @help("<I am an example>")
    def function_name(self):
        return


    # Example receptor method
    # The receptor decorator makes the defined method get autocalled
    # for any corresponding synapse. To see a list of available synapses
    # run tools/synapse.py or ask the bot for -synapse when running.
    @Receptor('heartbeat')
    def auto(self):
        return
