import os
import re
import pkgutil

from autonomic import axon, category, help, Dendrite
from settings import SAFESET, NICK, IDENT, HOST, REALNAME
from secrets import *
from util import colorize
from time import sleep


@category("system")
class System(Dendrite):
    def __init__(self, cortex):
        self.libs = [name for _, name, _ in pkgutil.iter_modules(['brainmeats'])]
        super(System, self).__init__(cortex)

    @axon
    @help("<show editable " + NICK + " settings>")
    def settings(self):
        for name, value in SAFESET:
            if self.values and name not in self.values:
                continue
            sleep(1)
            self.chat(name + " : " + str(value))

    @axon
    @help("SETTING=VALUE <update a " + NICK + " setting>")
    def update(self, inhouse=False):
        if not inhouse:
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

    @axon
    @help("<reload " + NICK + ">")
    def reload(self):
        self.cx.master.reload()

    @axon
    @help("<set squirrel on fire and staple it to angel. No, really>")
    def reboot(self):
        self.cx.master.die()

    @axon
    @help("NICKNAME <change " + NICK + "'s name>")
    def nick(self):
        if not self.values:
            self.chat("Change name to what?")
            return

        name = self.values[0]
        if not re.search("^\w+$", name):
            self.chat("Invalid name")
            return

        self.cx.sock.send('NICK ' + name + '\n')
        self.cx.sock.send('USER ' + IDENT + ' ' + HOST + ' bla :' + REALNAME + '\n')
        self.cx.sock.send('JOIN ' + CHANNEL + '\n')

        self.update(['NICK', name])
        self.reboot()

    @axon
    @help("<update from git repo>")
    def gitpull(self):
        os.system("git pull origin master")
        self.cx.master.reload(True)
        self.chat("I know kung-fu.")

    @axon
    @help("<show available libs and their status>")
    def meats(self):
        _libs = []
        for lib in self.libs:
            if lib not in self.cx.master.ENABLED:
                _libs.append(colorize(lib, 'red')) 
            else:
                _libs.append(colorize(lib, 'green')) 

        self.chat(', '.join(_libs))

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
        for lib in values:
            if lib in self.cx.master.ENABLED:
                already.append(lib) 
            elif lib not in self.libs:
                nonextant.append(lib)
            else:
                enabled.append(lib)
                self.cx.master.ENABLED.append(lib)

        messages = []
        if len(already):
            messages.append('%s already enabled.' % ', '.join(already))
            
        if len(nonextant):
            messages.append("%s don't exist." % ', '.join(nonextant))
            
        if len(enabled):
            messages.append("Enabled %s." % ', '.join(enabled))
            
        self.cx.master.reload(True)

        self.chat(' '.join(messages))

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
