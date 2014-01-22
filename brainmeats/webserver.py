import random
import os

from autonomic import axon, alias, category, help, Dendrite
from settings import ONETIME, WEBSITE, SERVER_RELOAD


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
    def chatlink(self):
        num = self._setaccess()
        link = WEBSITE + "/chatlogs?onetime=" + str(num)
        self.chat(link)

    @axon
    @help("<Get one-time link to error log>")
    def errorlink(self):
        num = self._setaccess()
        link = WEBSITE + "/errorlog?onetime=" + str(num)
        self.chat(link)

    @axon
    @help("<get link to appropriate [sic] http codes for describing dating>")
    def pigs(self):
        link = WEBSITE + "/codez"
        self.chat(link)

    @axon
    @help("<Reload uwsgi server>")
    def reloadserver(self):
        os.system('touch ' + SERVER_RELOAD)
        self.chat("Reloaded uwsgi")
