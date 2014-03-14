import sys
import socket
import cortex
import ssl

from config import load_config
from time import sleep, mktime, localtime

# Welcome to the beginning of a very strained brain metaphor!
# This is the shell for running the cortex. Ideally, this will never
# fail and you never have to reboot. Hah! I make funny, yes? More
# important, if you make changes to this file, you have to reboot as
# a reload won't change it.
class Medulla:
    def __init__(self):

        print '* Loading settings'
        self.settings = settings = load_config('config/settings.yaml')

        print '* Loading secrets'
        self.secrets = secrets = load_config('config/secrets.yaml')

        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print '* Pinging IRC'

        raw_socket.connect((settings.irc.host, settings.irc.port))

        if hasattr(settings.irc, 'ssl') and settings.irc.ssl:
            self.sock = ssl.wrap_socket(raw_socket)
        else:
            self.sock = raw_socket

        if hasattr(settings.irc, 'password') and settings.irc.password:
            self.sock.send('PASS %s\n' % settings.irc.password)

        self.sock.send('USER %s %s bla :%s\n' % (settings.bot.ident, settings.bot.ident, settings.bot.realname))
        self.sock.send('NICK %s\n' % settings.bot.nick)

        if hasattr(settings.irc, 'nickserv') and settings.irc.nickserv:
            self.sock.send('PRIVMSG %s :identify %s\n' % (settings.irc.nickserv.nick, settings.irc.nickserv.password))

        # Some servers require a pause prior to being able to join a channel
        sleep(2)

        self.sock.setblocking(0)


        self.ENABLED = self.settings.plugins.values()[0]
        self.active = True
        self.brain = cortex.Cortex(self)

        # The pulse file is set as a measure of how
        # long the bot has been spinning its gears
        # in a process. If it can't set the pulse
        # for too long, a signal kills it and reboots.
        # Note: this has become less of an issue
        # since all the bot's commands became threaded
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
            self.brain.act('strokes out.', False, self.secrets.owner)

        for channel in self.secrets.channels:
            name, attr = channel.popitem()
            if attr.primary:
                continue
            self.brain.brainmeats['channeling'].leave(name)

        self.active = False

        self.settings = settings = load_config('config/settings.yaml')
        self.secrets = secrets = load_config('config/secrets.yaml')

        import datastore
        import util
        import autonomic
        import cortex
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
            self.brain.act('comes to.', False, self.secrets.owner)

    def setpulse(self):
        self.lastpulse = mktime(localtime())
        pulse = open(self.settings.sys.pulse, 'w')
        pulse.write(str(self.lastpulse))
        pulse.close()

    def die(self, msg=None):
        if msg is not None:
            print msg
        sys.exit()

connect = Medulla()
