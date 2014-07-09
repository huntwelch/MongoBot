import os
import re
import pkgutil
import threading

from autonomic import axon, help, Dendrite, public, alias
#from settings import SAFESET, NICK, REGISTERED, CONTROL_KEY
from secrets import *
from util import colorize
from time import sleep


# TODO Remove this crap
SAFESET = []
NICK = 'REMOVE THIS'


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

    # Help menu. It used to just show every command, but there
    # are so goddamn many at this point, they had to be split
    # into categories.
    @axon
    @help("<show this menu>")
    @alias('help')
    def showhelp(self):

        enabled = self.cx.master.ENABLED
        broken = self.cx.broken

        if not self.values or self.values[0] not in self.libs:
            cats = sorted(self.libs)

            print 'Cats: %s' % cats
            print 'Enabled: %s' % enabled
            print 'Broken: %s' % broken


            cats = [colorize(lib, 'green') if lib in enabled else lib for lib in self.libs]
            cats = [colorize(lib, 'red') if lib in broken else lib for lib in cats]

            cats = ', '.join(cats)
            print cats
            self.chat('%shelp WHAT where WHAT is one of the following: %s' % (self.cx.settings.bot.command_prefix, cats))
            return

        which = self.values[0]
        if which in broken:
            return '%s is currently broken.' % which

        if which not in enabled:
            return '%s is not enabled.' % which

        return self.cx.helpmenu[which]

    @axon
    def threads(self):
        return threading.activeCount()

    @axon
    @help("<show editable settings>")
    def settings(self):
        for name, value in SAFESET:
            if self.values and name not in self.values:
                continue
            sleep(1)
            self.chat(name + " : " + str(value))

    # This should be pretty straightforward. Based on BOT_PASS
    # in secrets; nobody can use the bot until they're
    # registered. Went with flat file for ease of editing
    # and manipulation.
    @axon
    @public
    @help("PASSWORD <register your nick and host to use the bot>")
    def regme(self):
        if not self.values:
            self.chat("Please enter a password.")
            return

        if self.values[0] != BOT_PASS:
            self.chat("Not the password.")
            return

        real = self.cx.lastrealsender
        if real and real in self.cx.REALUSERS:
            self.chat("Already know you, bro.")
            return

        self.cx.REALUSERS.append(real)

#        users = open(REGISTERED, 'a')
#        users.write(real + "\n")
#        users.close()

        self.chat("You in, bro.")

    # Rewrite a setting in the settings file. Available settings
    # are defined in SAFESET. Do not put SAFESET in the SAFESET.
    # That's just crazy.
    @axon
    @help("SETTING=VALUE <update a bot setting>")
    def update(self, vals=False):
        if not vals:
            vals = self.values

        if not vals or len(vals) != 2:
            self.chat("Must name SETTING and value, please")
            return

        pull = ' '.join(vals)

        if pull.find("'") != -1 or pull.find("\\") != -1 or pull.find("`") != -1:
            self.chat("No single quotes, backtics, or backslashes, thank you.")
            return

        setting, value = pull.split(' ', 1)

        safe = False
        for safesetting, val in SAFESET:
            if setting == safesetting:
                safe = True
                break

        if not safe:
            self.chat("That's not a safe value to change.")
            return

        rewrite = "sed 's/" + setting + " =.*/" + setting + " = " + value + "/'"
        targeting = ' <settings.py >tmp'
        reset = 'mv tmp settings.py'

        os.system(rewrite + targeting)
        os.system(reset)

        self.chat(NICK + " rewrite brain. Feel smarter.")

    # Reloads the bot. Any changes make to cortex or brainmeats
    # and most settings will be reflected after a reload.
    @axon
    @help('<reload %NICK%>')
    def reload(self):
        meats = self.cx.brainmeats
        if 'webserver' in meats:
            meats['webserver'].reloadserver(True)
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
        os.system("git pull origin master")
        self.cx.master.reload(True)
        self.chat("I know kung-fu.")

    # Turn libs on.
    @axon
    @help("LIB_1 [LIB_n] <activate libraries>")
    def enable(self):
        if not self.values:
            self.chat("Enable what?")
            return

        if self.values[0] == '*':
            values = self.libs
        else:
            values = self.values

        already = []
        nonextant = []
        enabled = []
        broken = []
        for lib in values:
            if lib in self.cx.master.ENABLED:
                already.append(lib)
            elif lib not in self.libs:
                nonextant.append(lib)
            elif lib in self.cx.broken:
                broken.append(lib)
            else:
                enabled.append(lib)
                self.cx.master.ENABLED.append(lib)

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
            self.chat("Disable what?")
            return

        if 'system' in self.values:
            self.chat("You can't disable the system, jackass.")
            return

        already = []
        nonextant = []
        disabled = []
        for lib in self.values:
            if lib not in self.libs:
                nonextant.append(lib)
            elif lib not in self.cx.master.ENABLED:
                already.append(lib)
            else:
                disabled.append(lib)
                self.cx.master.ENABLED.remove(lib)

        messages = []
        if len(already):
            messages.append('%s already disabled.' % ', '.join(already))

        if len(nonextant):
            messages.append("%s don't exist." % ', '.join(nonextant))

        if len(disabled):
            messages.append("Disabled %s." % ', '.join(disabled))

        self.cx.master.reload(True)

        self.chat(' '.join(messages))

    # Show secret stuff.
    @axon
    @help("<print api keys and stuff>")
    def secrets(self):
        # TODO: lot of new secrets, add them, or list them and get specific one from values
        items = {
            'WEATHER_API': WEATHER_API,
            'WORDNIK_API': WORDNIK_API,
            'FML_API': FML_API,
            'WOLFRAM_API': WOLFRAM_API,
            'DELICIOUS_USER ': DELICIOUS_USER,
            'DELICIOUS_PASS ': DELICIOUS_PASS,
        }
        for key, val in items.iteritems():
            self.chat(key + ": " + val)
