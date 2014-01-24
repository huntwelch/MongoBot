import sys
import socket
import settings
import cortex
import os
import thread
import ssl

from settings import NICK, IDENT, HOST, PORT, CHANNEL, REALNAME, OWNER, SMS_LOCKFILE, PULSE, ENABLED
from time import sleep, mktime, localtime


class Medulla:
    def __init__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Could write disabled to a file for persistance between reboots 
        self.ENABLED = ENABLED

        print "* Pinging IRC"

        sock.connect((HOST, PORT))

        self.sock = sock

        self.sock.send('NICK ' + NICK + '\n')
        self.sock.send('USER ' + IDENT + ' ' + HOST + ' bla :' + REALNAME + '\n')
        self.sock.send('JOIN ' + CHANNEL + '\n')

        self.sock.setblocking(0)

        self.active = True
        self.brain = cortex.Cortex(self)

        print "* Establishing pulse"
        self.setpulse()

        print "* Running monitor"

        while True:
            sleep(0.1)
            self.brain.monitor()
            if mktime(localtime()) - self.lastpulse > 10:
                self.setpulse()

    def reload(self, quiet=False):
        if self.brain.values and len(self.brain.values[0]):
            quiet = True

        if not quiet:
            self.brain.act("strokes out.")
        else:
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

    def setpulse(self):
        self.lastpulse = mktime(localtime())
        pulse = open(PULSE, 'w')
        pulse.write(str(self.lastpulse))
        pulse.close()

    def die(self):
        sys.exit()

connect = Medulla()
