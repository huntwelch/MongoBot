import random
import os
import pyotp
import base64

from autonomic import axon, alias, category, help, Dendrite
from settings import WEBSITE, SERVER_RELOAD
from secrets import HTTP_PASS

@category("webserver")
class Webserver(Dendrite):
    def __init__(self, cortex):
        self.totp = pyotp.TOTP(base64.b32encode(HTTP_PASS), interval=600)
        super(Webserver, self).__init__(cortex)

    def _setaccess(self):
        return self.totp.now()

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
