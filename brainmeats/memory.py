from autonomic import axon, category, help, Dendrite


@category("memory")
class Memory(Dendrite):
    def __init__(self, cortex):
        super(Memory, self).__init__(cortex)

    @axon
    @help("<search logs for phrase and print the most recent>")
    def mem(self):
        if not self.values:
            self.chat("Something about what?")
            return

        self.chat("Recalling...")
        self.memories = []
        thinkingof = ' '.join(self.values)
        for line in open(LOG):
            if line.find(thinkingof) != -1:
                try:
                    whom, message = line[1:].split(":", 1)
                except:
                    continue
                if message.find("~somethingabout") == 0:
                    continue
                whom = whom.split("!")[0]
                self.memories.append(whom + ": " + message)
        self.memories.pop()
        self.mempoint = len(self.memories) - 1
        self.remember()

    @axon
    @help("<after mem, get the next phrase memory>")
    def next(self):
        if self.nomem():
            return
        if self.mempoint == len(self.memories) - 1:
            self.chat("That's the most recent thing I can remember.")
            return
        self.mempoint += 1
        self.remember()

    @axon
    @help("<after mem, get the previous phrase memory>")
    def prev(self):
        if self.nomem():
            return
        if self.mempoint == 0:
            self.chat("That's as far back as I can remember.")
            return
        self.mempoint -= 1
        self.remember()

    @axon
    @help("<after mem, get the latest phrase memory>")
    def oldest(self):
        if self.nomem():
            return
        self.mempoint = 0
        self.remember()

    @axon
    @help("<you see where this is going>")
    def latest(self):
        if self.nomem():
            return
        self.mempoint = len(self.memories) - 1
        self.remember()

    def remember(self):
        try:
            self.chat(self.memories[self.mempoint])
        except:
            self.chat("Don't recall anything about that.")

    def nomem(self):
        if not self.memories:
            self.chat("Nothing in memory.")
            return True
        else:
            return False
