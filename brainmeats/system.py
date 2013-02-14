import os
import re

from time import sleep
from autonomic import axon, category, help, Dendrite
from settings import SAFESET, NICK, IDENT, HOST, REALNAME, CHANNEL


@category("system")
class System(Dendrite):
    def __init__(self, cortex):
        super(System, self).__init__(cortex)

    @axon
    @help("[setting]+ <show editable " + NICK + " settings>")
    def settings(self):
        self.snag()

        for name, value in SAFESET:
            if self.values and name not in self.values:
                continue
            sleep(1)
            self.chat(name + " : " + str(value))

    @axon
    @help("<update a " + NICK + " setting>")
    def update(self, inhouse=False):
        if not inhouse:
            self.snag()
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
    @help("<change " + NICK + "'s name>")
    def nick(self):
        self.snag()

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
