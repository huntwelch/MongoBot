from autonomic import axon, alias, help, Dendrite, public


class Channeling(Dendrite):

    mods = ['spy', 'command', 'speak']
    chan = False

    def __init__(self, cortex):
        super(Channeling, self).__init__(cortex)


    def massage(self, channel):
        if channel[:1] != '#':
            channel = '#' + channel
        return channel


    @axon
    @alias('mods')
    @help('<Get list of available mods>')
    def getmods(self):
        return ', '.join(self.mods)


    @axon
    @help('<Get list of channels and mods applied>')
    def chanstat(self):
        message = ['Connected to %s channels.' % len(self.cx.channels)]
        for channel in self.cx.channels:
            message.append('%s (%s)' % (channel, ', '.join(self.cx.channels[channel].mods)))

        return message


    @axon
    @alias('part')
    @help('CHANNEL <leave CHANNEL>')
    @public
    def leave(self, channel=False):
        if not self.values and not channel:
            return 'Leave what?'

        if not channel:
            channel = self.massage(self.values.pop(0))

        if channel not in self.cx.channels:
            return 'Not in that channel'

        del self.cx.channels[channel]
        self.cx.master.sock.send('PART %s\n' % channel)

        return 'Left %s' % channel


    # Join another channel
    @axon
    @public
    @help('CHANNEL [MOD1...MODN] <join CHANNEL, optionally add mods>')
    def join(self, channel=False):
        if not self.values and not channel:
            return 'Join what?'

        if not channel:
            channel = self.massage(self.values.pop(0))

        self.cx.master.sock.send('JOIN %s\n' % channel)

        if channel in self.cx.channels:
            return 'Already in that channel'

        self.cx.channels[channel] = {'mods':[]}

        if self.values:
            self.modchan(channel, self.values)

        return 'Joined %s' % channel


    @axon
    @help('CHANNEL +MOD1 [-MOD2...+MODN] <add or remove mods on joined channel>')
    def modchan(self, chan=False, what=False):

        if not chan and not self.values:
            return 'Mod what?'

        if not what and not self.values:
            return 'Mod how?'

        if not what and not chan and len(self.values) < 2:
            return 'Usage: .modchan #channel +mod1 -mod2'

        if not chan:
            chan = self.massage(self.values.pop(0))

        if 'primary' in self.cx.channels[chan]:
            return 'You cannot modify the main channel with this command.'

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
                self.cx.channels[chan]['mods'].append(mod)

            if action == '-' and mod in self.cx.channels[chan]:
                self.cx.channels[chan]['mods'].remove(mod)

        return 'Mods applied to %s' % chan


    @axon
    @alias('m')
    @help('CHANNEL MESSAGE <speak to channel>')
    def talkchannel(self):
        if not self.values or len(self.values) < 2:
            return 'Format as #channel your message'


        channel = self.massage(self.values.pop(0))
        message = ' '.join(self.values)

        if channel not in self.cx.channels:
            return 'Not in that channel'

        self.chat(message, channel)
        return 'Message sent'
