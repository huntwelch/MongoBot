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
    @help("<Get one-time link history page>")
    def history(self):
        num = self._setaccess()
        link = "The history of okdrink: %s/history?onetime=%s" % (self.config.url, str(num))
        self.chat(link)


    @axon
    @help("<Get one-time link to chat log>")
    def chatlink(self):
        num = self._setaccess()
        link = "%s/chatlogs?onetime=%s" % (self.config.url, str(num))
        self.chat(link)


    @axon
    @help("<Get one-time link to defaults (.set commands)>")
    def defaultslink(self):
        num = self._setaccess()
        link = "%s/defaults?onetime=%s" % (self.config.url, str(num))
        self.chat(link)


    @Receptor('twitch')
    def getuploads(self):
        file = '/tmp/uploads.msgs'
        if not os.path.isfile(file): return
        if os.stat(file).st_size == 0: return

        with open(file) as f:
            msgs = f.readlines()

        f.close()

        if msgs:
            os.remove(file)

        msgs = [x.strip() for x in msgs]
        msgs = ', '.join(msgs)

        self.chat(msgs, target=self.cx.secrets.primary_channel)


    @axon
    @help("<Get one-time link to quote list>")
    def quotelink(self):
        num = self._setaccess()
        link = "%s/quotes?onetime=%s" % (self.config.url, str(num))
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
        os.system('touch %s' % self.config.reloader)
        if not quiet:
            self.chat("Reloaded uwsgi")
