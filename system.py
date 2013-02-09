from autonomic import axon, category, help, Dendrite
from settings import SAFESET, NICK


@category("system")
class System(Dendrite):
    def __init__(self, cortex):
        super(System, self).__init__(cortex) 
        self.master = cortex.master

    @axon
    @help("<show editable " + NICK + " settings>")
    def settings(self):
        for name, value in SAFESET:
            sleep(1)
            self.chat(name + " : " + str(value))

    @axon
    @help("<update a " + NICK + " setting>")
    def update(self):
        self.snag()

        if not self.values or len(self.values) != 2:
            self.chat("Must name SETTING and value, please")
            return

        pull = ' '.join(self.values)

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
        self.master.reload()

    @axon
    @help("<set squirrel on fire and staple it to angel. No, really>")
    def reboot(self):
        self.master.die()


