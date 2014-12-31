import os
import re
import pkgutil
import threading

from autonomic import axon, help, Dendrite, public, alias
from cybernetics import metacortex
from util import colorize
from time import sleep


# System is stuff relating to the function of the
# the bot and the server. There's some potentially
# dangerous shit in here.
class System(Dendrite):

    libs = [name for _, name, _ in pkgutil.iter_modules(['brainmeats'])]

    def __init__(self, cortex):
        super(System, self).__init__(cortex)


    @axon
    @alias('raw')
    def rawsock(self):
        if not self.values:
            return 'Send what?'

        self.cx.sock.send(' '.join(self.values))


    @axon
    def echo(self):
        return ' '.join(self.values)


    # Help menu. It used to just show every command, but there
    # are so goddamn many at this point, they had to be split
    # into categories.
    @axon
    @help("<show this menu>")
    @alias('help')
    def showhelp(self):

        enabled = self.cx.enabled
        broken = self.cx.broken

        if not self.values or self.values[0] not in self.libs or self.values[0] not in self.cx.helpmenu:
            cats = sorted(self.libs)

            cats = [colorize(lib, 'green') if lib in enabled else lib for lib in self.libs]
            cats = [colorize(lib, 'red') if lib in broken else lib for lib in cats]

            cats = ', '.join(cats)

            return '%shelp WHAT where WHAT is one of the following: %s' % (self.cx.settings.bot.command_prefix, cats)

        which = self.values[0]
        if which in broken:
            return '%s is currently broken.' % which

        if which not in enabled:
            return '%s is not enabled.' % which

        return self.cx.helpmenu[which]


    # This doesn't work. Go figure.
    @axon
    def threads(self):
        return threading.activeCount()


    # Reloads the bot. Any changes make to cortex or brainmeats
    # and most settings will be reflected after a reload.
    @axon
    @help('<reload %s>' % metacortex.botnick)
    def reload(self):
        meats = self.cx.brainmeats
        # Don't know why this is broken
        #if 'webserver' in meats:
        #    meats['webserver'].reloadserver(True)
        self.cx.master.reload()


    # Actually kills the medulla process and waits for the
    # doctor to restart. Some settings and any changes to
    # medulla.py won't take effect until a reboot.
    @axon
    @alias('seppuku', 'harakiri')
    @help("<set squirrel on fire and staple it to angel. No, really>")
    def reboot(self):
        self.cx.master.die()


    # DANGER ZONE. You merge it, anyone can pull it. If you
    # have a catastrophic failure after this, it's probably
    # because of a conflict with local changes. But will it
    # tell you that's what happened? HELL no.
    @axon
    @help("<update from git repo>")
    def gitpull(self):
        if not self.values:
            return 'Which branch?'

        branch = self.values[0]

        os.system("git pull origin %s" % branch)
        self.cx.master.reload(True)
        self.chat("I know kung-fu.")


    # Turn libs on.
    @axon
    @help("LIB_1 [LIB_n] <activate libraries>")
    def enable(self):
        if not self.values:
            return "Enable what?"

        if self.values[0] == '*':
            values = self.libs
        else:
            values = self.values

        already = []
        nonextant = []
        enabled = []
        broken = []
        for lib in values:
            if lib in self.cx.enabled:
                already.append(lib)
            elif lib not in self.libs:
                nonextant.append(lib)
            elif lib in self.cx.broken:
                broken.append(lib)
            else:
                enabled.append(lib)
                self.cx.enabled.append(lib)

        messages = []
        if len(already):
            messages.append('%s already enabled.' % ', '.join(already))

        if len(nonextant):
            messages.append('%s nonexistent.' % ', '.join(nonextant))

        if len(broken):
            messages.append('%s done borked.' % ', '.join(broken))

        if len(enabled):
            messages.append('Enabled %s.' % ', '.join(enabled))

        self.cx.master.reload(True)

        self.chat(' '.join(messages))


    # Turn libs off. Why all this lib stuff? Helps when developing, so
    # you can just turn stuff off while you tinker and prevent crashes.
    @axon
    @help("LIB_1 [LIB_n] <deactivate libraries>")
    def disable(self):
        if not self.values:
            return "Disable what?"

        if 'system' in self.values:
            return "You can't disable the system, jackass."

        already = []
        nonextant = []
        disabled = []
        for lib in self.values:
            if lib not in self.libs:
                nonextant.append(lib)
            elif lib not in self.cx.enabled:
                already.append(lib)
            else:
                disabled.append(lib)
                self.cx.enabled.remove(lib)

        messages = []
        if len(already):
            messages.append('%s already disabled.' % ', '.join(already))

        if len(nonextant):
            messages.append("%s don't exist." % ', '.join(nonextant))

        if len(disabled):
            messages.append("Disabled %s." % ', '.join(disabled))

        self.cx.master.reload(True)

        self.chat(' '.join(messages))
