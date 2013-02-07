from autonomic import axon, category, help, Dendrite


@category("")
class NAME(Dendrite):
    def __init__(self, cortex):
        super(NAME, self).__init__(cortex) 

    @axon
    @help("<>")
    def func(self):
        # when cortex variables are needed
        self.snag()
