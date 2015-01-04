import re
import os
import shutil
import pkgutil
import string
import traceback

from datetime import date, timedelta
from time import time, mktime, localtime
from random import randint
from config import load_config
from getpass import getpass

from datastore import connectdb
from util import ratelimited, zalgo
from staff import Butler
from autonomic import serotonin, Neurons, Synapse
from cybernetics import metacortex
from id import Id


# Basically all the interesting interaction with
# irc and command / content parsing happens here.
# Also connects to mongodb.
class Cortex:

    context = False

    master = False
    thalamus = False
    values = False
    lastpublic = False
    lastprivate = False
    lastchat = False
    lastsender = False
    lastrealsender = False
    gettingnames = True
    memories = False
    autobabble = False
    lastcommand = False
    joined = False
    operator = False
    bequiet = False
    lastip = False

    butler = False

    channels = []
    public_commands = []
    members = []
    broken = []
    realuserdata = []
    enabled = []

    flags = {}
    commands = {}
    live = {}
    helpmenu = {}

    boredom = int(mktime(localtime()))
    namecheck = int(mktime(localtime()))

    def __init__(self, master, electroshock=False):

        print '* Initializing'
        self.master = master
        self.settings = master.settings
        self.secrets = master.secrets
        self.channels = self.secrets.channels
        self.context = self.secrets.primary_channel
        self.personality = self.settings.bot

        self.enabled = self.settings.plugins.values().pop(0)

        metacortex.botnick = self.personality.nick

        print '* Exciting neurons'
        Neurons.cortex = self

        print '* Connecting to datastore'
        connectdb()

        print '* Fondly remembering daddy'
        admin = Id(self.secrets.owner)
        if not admin.password:
            print '*' * 40
            print 'Hey %s! You haven\'t set a password yet! As my daddy you really need a password.' % self.secrets.owner
            tmp_pass = getpass('Before I can continue, please enter a password: ')
            print 'See? Was that so hard?'
            admin.setpassword(tmp_pass, True)
            tmp_pass = None

        print '* Loading brainmeats'
        self.loadbrains(electroshock)

        print '* Waking butler'
        self.butler = Butler(self)


    # Loads up all the files in brainmeats and runs them
    # through the hookup process.
    def loadbrains(self, electroshock=False):
        self.brainmeats = {}
        brainmeats = __import__('brainmeats', fromlist=[])
        if electroshock:
            reload(brainmeats)

        areas = [name for _, name, _ in pkgutil.iter_modules(['brainmeats'])]

        for area in areas:
            print '{0: <25}'.format('  - %s' % area),

            if area not in self.enabled:
                print '[\033[93mDISABLED\033[0m]'
                continue

            try:
                mod = __import__('brainmeats', fromlist=[area])
                mod = getattr(mod, area)
                if electroshock:
                    reload(mod)
                cls = getattr(mod, area.capitalize())
                self.brainmeats[area] = cls(self)
                print '[\033[0;32mOK\033[0m]'
            except Exception as e:
                self.chat('Failed to load %s.' % area, error=str(e))
                self.broken.append(area)
                self.enabled.remove(area)
                print '[\033[0;31mFAILED\033[0m]'
                if self.settings.debug.verbose:
                    print e
                    print traceback.format_exc()

        for brainmeat in self.brainmeats:
            serotonin(self, brainmeat, electroshock)


    # When you get amnesia, it's probably a good time to really
    # think and try to remember who you are.
    def amnesia(self):

        # This is an easy way out for now...
        return self.personality


    # And this is the basic function that runs all the time.
    # The razor qualia edge of consciousness, if you will
    # (though you shouldn't). It susses out the important
    # info, logs the chat, sends PONG, finds commands, and
    # decides whether to send new information to the parser.
    @Synapse('twitch')
    def monitor(self):
        self.thalamus.process()


    # If it is indeed a command, the cortex stores who sent it,
    # and any words after the command are split in a values array,
    # accessible by the brainmeats as self.values.
    multis = 0

    def command(self, sender, cmd, piped=False, silent=False):

        # Limit commands to allowed channels.
        if self.context in self.channels \
            and 'command' not in self.channels[self.context]['mods']:
                return

        # This handles piping. Piping just breaks
        # off the first command, gathers its output
        # and runs command again on the next part
        # of the chain until it's done.
        chain = cmd.split('|', 1)
        pipe = False

        if len(chain) is 2:
            cmd = chain[0].strip()
            pipe = chain[1].strip()

        if piped:
            cmd = '%s %s' % (cmd, piped)

        components = cmd.split()

        _what = components.pop(0)

        what = _what[1:]
        means = _what[:1]

        # These are specific command malformations
        # that cropped up.
        is_nums = re.search("^[0-9]+", what)
        is_breaky = re.search("^" + re.escape(self.personality.command_prefix) + "|[^\w]+", what)

        if is_nums or is_breaky:
            return

        # Small convenience feature.
        if not what:
            if not self.lastcommand:
                return
            what = self.lastcommand

        self.values = False
        self.flags = {}
        flags = []

        if components:
            for component in components:
                if component[:1] == self.personality.flag_prefix:
                    flags.append(component)

            self.values = components

        # An awesome feature that's not used at all. Should be.
        if flags:
            for flag in flags:
                self.values.remove(flag)
                value = True
                if '=' in flag:
                    flag, value = flag.split('=')
                flag = flag[1:]
                self.flags[flag] = value

        self.logroom('%s sent command: %s\n' % (sender, what))
        self.lastsender = sender
        self.lastcommand = what

        result = None

        # So you'll notice that some commands return
        # values that this function sorts out into chats,
        # while other commands directly run the self.chat,
        # ._act, and .announce functions attached by the
        # Dendrite class. Well, it used to be just those
        # self.chat(whatever) and return, because it's a bot,
        # right? It's final output is a chat, otherwise it's
        # not much of a chatbot.
        #
        # Then some asshole in our chatroom said something
        # like "it'd be cool if we could pipe commands, like
        # -tweet | babble or something."
        #
        # So THAT got stuck in my head even though it's
        # totally ridiculous, but I won't be able to sleep
        # until it's fully implemented, and the first step
        # in that is the ability to do something besides
        # just chat out at the end of the function. If it's
        # being piped, the best way to do that is reset
        # self.values to the result of the command if it's
        # piped from or to a pipeable function (I know
        # 'from or to' should be one or the other, but it's
        # 1am and I'm drunkenly listening to the Nye vs.
        # Ham debate over youtube and it's almost as
        # upsetting as realizing I'm going to have to comb
        # over every goddamn function in this bot to
        # determine what's pipeable and change its output).
        #
        # Point is, you can return a list or a string at
        # the end of a brainmeat command, or just use chat.
        # I probably won't worry about act and announce.
        if means == self.personality.multi_command_prefix:

            # The multi checking had to be put in
            # after Eli decided to enter this:
            # .babble fork | :babble | :babble | :babble
            # ... which of course spiked the redis server
            # to 100% CPU and eventually flooded the chat
            # room with n^4 chats until the bot had to be
            # kicked. This is what happens when you try
            # to give nice things to hackers.
            self.multis += 1
            if self.multis > 1:
                self.chat('This look like fork bomb. You kick puppies too?')
                self.multis = 0
                return

            result = []

            if not components:
                self.chat("No args to iter. Bitch.")
                self.multis = 0
                return

            for item in components:
                self.values = [item]
                _result = self.commands.get(what, self.default)()
                result.append(_result)
        else:
            try:
                result = self.commands.get(what, self.default)()
            except Exception as e:
                self.chat(str(e))
                print traceback.format_exc()

        if not result:
            return

        if pipe:
            # Piped output must be string
            if type(result) is list:
                result = ' '.join(result)
            self.command(sender, pipe, result)
            return

        if type(result) in [str, unicode]:
            if silent:
                return result

            self.chat(result)

        if type(result) is list:
            if len(result) > self.personality.throttle:
                result = result[:self.personality.throttle]
                result.append("Such result. So self throttle. Much erotic. Wow.")

            for line in result:
                self.chat(line)

        self.multis = 0

    # Careful with this one.
    def bored(self):
        if not self.members:
            return

        self.announce('Chirp chirp. Chirp Chirp.')

    # Simple log for room activity.
    def logroom(self, what):
        with open(self.settings.directory.log, 'a') as f:
            f.write('TS:%s;%s' % (time(), what))

        now = date.today()
        if now.day != 1:
            return

        prev = date.today() - timedelta(days=1)
        backlog = '%s/%s-mongo.log' % (self.settings.directory.logdir, prev.strftime('%Y%m'))

        if os.path.isfile(backlog):
            return

        shutil.move(self.settings.directory.log, backlog)

    # Announce means the chat is always sent to the channel,
    # never back as a private response.
    @ratelimited(2)
    def announce(self, message):
        self.chat(message, target=self.secrets.primary_channel)

    # Since chat is mongo's only means of communicating with
    # a room, the ratelimiting here should prevent any overflow
    # violations.
    # NOTE: 'and not target' may be a sketchy override.
    @ratelimited(2)
    def chat(self, message, target=False, error=False):

        if self.context in self.channels \
            and not target \
            and 'speak' not in self.channels[self.context]['mods']:
                return

        if self.bequiet:
            return

        if not message:
            return

        if target:
            whom = target
        elif self.context in self.channels:
            whom = self.context
        else:
            user = Id(self.lastsender)
            whom = user.nick

        if randint(1, 170) == 13:
            message = zalgo(message)

        filter(lambda x: x in string.printable, message)

        try:
            message = message.encode('utf-8')
            self.logroom('___%s: %s\n' % (self.personality.nick, str(message)))
            m = str(message)
            if randint(1, 170) == 23:
                i = m.split()
                pos = randint(0, len(i))
                i.insert(pos, 'fnord')
                m = ' '.join(i)

            if error:
                m += ' %s' % str(error)

            self.thalamus.send('PRIVMSG %s :%s' % (whom, m))
        except Exception as e:
            try:
                self.thalamus.send('PRIVMSG %s :ERROR: ' % (whom, str(e)))
            except:
                pass

    def act(self, message, public=False, target=False):
        message = '\001ACTION %s\001' % message
        if public:
            self.announce(message, target)
        elif target:
            self.chat(message, target)
        else:
            self.chat(message)

    # When all else fails.
    def default(self):
        self.act(" cannot do this thing :'(")
