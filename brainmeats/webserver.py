import random

from autonomic import axon, alias, category, help, Dendrite
from settings import ONETIME, WEBSITE


@category("webserver")
class Webserver(Dendrite):
    def __init__(self, cortex):
        super(Webserver, self).__init__(cortex)

    def _setaccess(self):
        f = open(ONETIME, 'w')
        num = random.random()
        f.write(str(num))
        return num

    @axon
    @help("<Get one-time link to chat log>")
    def linklog(self):
        num = self._setaccess()
        link = WEBSITE + "/chatlogs?onetime=" + str(num)
        self.chat(link)
