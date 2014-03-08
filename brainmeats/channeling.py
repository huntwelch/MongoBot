from autonomic import axon, alias, help, Dendrite

# TODO: add leave room command, plus speaktoroom through him

class Channeling(Dendrite):

    mods = ['spy', 'command', 'speak']
    chan = False

    def __init__(self, cortex):
        super(Channeling, self).__init__(cortex)

    def massage(self, channel):
        if channel[:1] != '#':
            channel = '#' + channel
        return channel

    # Join another channel
    @axon
    def join(self, channel=False):
        if not self.values and not channel:
            return 'Join what?'

        if not channel:
            channel = self.massage(self.values.pop(0))

        self.cx.sock.send('JOIN %s\n' % channel)

        if channel not in self.cx.channels:
            self.cx.channels[channel] = []

        if self.values:
            self.modchan(channel, self.values)

        return 'Joined %s' % channel

    @axon
    def modchan(self, chan=False, what=False):

        if not chan and not self.values:
            self.chat('Mod what?')
            return

        if not what and not self.values:
            self.chat('Mod how?')
            return

        if not what and not chan and len(self.values) < 2:
            self.chat('Usage: -modchan #channel +mod1 -mod2')
            return

        if not chan:
            chan = self.massage(self.values.pop(0))

        if not what:
            what = self.values

        for mod in what:
            action = mod[:1]
            if action not in ['-', '+']:
                action = '+'
            else:
                mod = mod[1:]

            if mod not in self.mods:
                self.chat('%s is not a mod. Available mods: %s' % (mod, ', '.join(self.mods)))
                continue
        
            if action == '+' and mod not in self.cx.channels[chan]:
                self.cx.channels[chan].append(mod)
                
            if action == '-' and mod in self.cx.channels[chan]:
                self.cx.channels[chan].remove(mod)
                
        return 'Mods applied to %s' % chan
