import sys
import socket
import settings
import cortex
import os
import thread
import ssl

from settings import NICK, HOST, PORT, CHANNEL, SMS_LOCKFILE, PULSE, ENABLED
from secrets import IDENT, REALNAME, OWNER
from time import sleep, mktime, localtime


# Welcome to the beginning of a very strained brain metaphor!
# This is the shell for running the cortex. Ideally, this will never
# fail and you never have to reboot. Hah! I make funny, yes? More 
# important, if you make changes to this file, you have to reboot as
# a reload won't change it.
class Medulla:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print '* Pinging IRC'

        self.sock.connect((HOST, PORT))

        self.sock.send('NICK %s\n' % NICK)
        self.sock.send('USER %s %s bla :%s\n' % (IDENT, HOST, REALNAME))
        self.sock.send('JOIN %s\n' % CHANNEL)

        self.sock.setblocking(0)

        self.ENABLED = ENABLED
        self.active = True
        self.brain = cortex.Cortex(self)

        # The pulse file is set as a measure of how
        # long the bot has been spinning its gears
        # in a process. If it can't set the pulse
        # for too long, a signal kills it and reboots.
        print '* Establishing pulse'
        self.setpulse()

        print '* Running monitor'

        while True:
            sleep(0.1)
            self.brain.monitor()
            if mktime(localtime()) - self.lastpulse > 10:
                self.setpulse()

    # Reload has to be run from here to update the
    # cortex.
    def reload(self, quiet=False):
        if self.brain.values and len(self.brain.values[0]):
            quiet = True

        if not quiet:
            self.brain.act('strokes out.')
        else:
            self.brain.act('strokes out.', False, OWNER)

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
        self.brain.getnames()

        self.active = True

        if not quiet:
            self.brain.act('comes to.')
        else:
            self.brain.act('comes to.', False, OWNER)

    def setpulse(self):
        self.lastpulse = mktime(localtime())
        pulse = open(PULSE, 'w')
        pulse.write(str(self.lastpulse))
        pulse.close()

    def die(self):
        sys.exit()

connect = Medulla()
