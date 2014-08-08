import random
import os

from autonomic import axon, alias, help, Dendrite, Cerebellum, Receptor
from server.helpers import totp


# Allz the webs stuff.
@Cerebellum
class Webserver(Dendrite):

    def __init__(self, cortex):
        super(Webserver, self).__init__(cortex)

    def _setaccess(self):
        return totp.now()

    @axon
    @help("<Get one-time link to chat log>")
    def chatlink(self):
        num = self._setaccess()
        link = "%s/chatlogs?onetime=%s" % (self.config.url, str(num))
        self.chat(link)

    @axon
    @help("<Get one-time link to error log>")
    def errorlink(self):
        num = self._setaccess()
        link = "%s/errorlog?onetime=%s" % (self.config.url, str(num))
        self.chat(link)

    @axon
    @help("<get link to appropriate [sic] http codes for describing dating>")
    def pigs(self):
        link = "%s/codez" % self.config.url
        self.chat(link)

    @axon
    @help("<Reload uwsgi server>")
    def reloadserver(self, quiet=False):
        os.system('touch %' % self.config.reloader)
        if not quiet:
            self.chat("Reloaded uwsgi")
