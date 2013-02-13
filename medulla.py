import sys
import socket
import settings
import cortex

from settings import NICK, IDENT, HOST, PORT, CHANNEL, REALNAME, OWNER


class Medulla:
    def __init__(self):
        self.sock = socket.socket()

        print "* Pinging IRC"

        self.sock.connect((HOST, PORT))
        self.sock.send('NICK ' + NICK + '\n')
        self.sock.send('USER ' + IDENT + ' ' + HOST + ' bla :' + REALNAME + '\n')
        self.sock.send('JOIN ' + CHANNEL + '\n')

        self.brain = cortex.Cortex(self)
        self.active = True

        while True and self.active:
            self.brain.monitor(self.sock)

    def reload(self):
        quiet = False
        if not self.brain.values or not len(self.brain.values[0]):
            self.brain.act("strokes out.")
        else:
            quiet = True
            self.brain.act("strokes out.", False, OWNER)

        self.active = False

        import settings
        import secrets
        import datastore
        import util
        import autonomic
        import cortex
        reload(settings)
        reload(secrets)
        reload(datastore)
        reload(autonomic)
        reload(util)
        reload(cortex)
        self.brain = cortex.Cortex(self)
        self.brain.loadbrains(True)

        self.active = True

        if not quiet:
            self.brain.act("comes to.")
        else:
            self.brain.act("comes to.", False, OWNER)

    def die(self):
        sys.exit()

connect = Medulla()
