import os
import re
import shutil
import pkgutil
import socket
import time
import string

from datetime import date, timedelta, datetime
from pytz import timezone
from time import mktime, localtime, sleep
from random import randint

from settings import SAFE, NICK, CONTROL_KEY, LOG, LOGDIR, PATIENCE, SCAN, STORE_URLS, \
    STORE_IMGS, IMGS, REGISTERED, TIMEZONE
from secrets import CHANNEL, OWNER, REALNAME, MEETUP_NOTIFY
from datastore import Drinker, connectdb
from util import unescape, shorten, ratelimited, postdelicious, savefromweb, \
    Browse
from autonomic import serotonin


# Basically all the interesting interaction with
# irc and command / content parsing happens here.
# Also connects to mongodb.
class Cortex:

    context = CHANNEL

    master = False
    sock = False
    values = False
    lastpublic = False
    replysms = False
    lastprivate = False
    lastsender = False
    gettingnames = True
    memories = False
    autobabble = False
    lastcommand = False

    public_commands = []
    members = []
    guests = [] 
    broken = []
    REALUSERS = []

    commands = {}
    live = {}
    helpmenu = {}

    boredom = int(mktime(localtime()))
    namecheck = int(mktime(localtime()))

    def __init__(self, master):

        print '* Initializing'
        self.master = master
        self.sock = master.sock

        print '* Loading brainmeats'
        self.loadbrains()

        print '* Loading users'
        users = open(REGISTERED, 'r')
        self.REALUSERS = users.read().splitlines()
        users.close()

        print '* Connecting to datastore'
        connectdb()

    # Loads up all the files in brainmeats and runs them 
    # through the hookup process.
    def loadbrains(self, electroshock=False):
        self.brainmeats = {}
        brainmeats = __import__('brainmeats', fromlist=[])
        if electroshock:
            reload(brainmeats)

        areas = [name for _, name, _ in pkgutil.iter_modules(['brainmeats'])]

        for area in areas:
            if area not in self.master.ENABLED:
                continue

            print area
            try:
                mod = __import__('brainmeats', fromlist=[area])
                mod = getattr(mod, area)
                if electroshock:
                    reload(mod)
                cls = getattr(mod, area.capitalize())
                self.brainmeats[area] = cls(self)
            except Exception as e:
                self.chat('Failed to load %s.' % area, error=str(e))
                self.broken.append(area)
                print 'Failed to load %s.' % area
                print e

        for brainmeat in self.brainmeats:
            serotonin(self, brainmeat, electroshock)

    # I'll be frank, I don't have that great a grasp on
    # threading, and despite working with people who do,
    # there were a number of live processes that thread
    # solutions weren't solving.
    #
    # The solution was to have everything that needs to 
    # run live run on one ticker. If you need something
    # to run continuously, add this to the __init__ of
    # your brainmeat:
    #
    # self.cx.addlive(self.ticker)
    #
    # ticker being the function in the class that runs.
    # see brainmeats/sms.y for a good example of this.
    def addlive(self, func, alt=False):
        name = alt or func.__name__
        self.live[name] = func

    def droplive(self, name):
        self.live.remove(name)

    # Core automatic stuff. I firmly believe boredom to
    # be a fundamental process in both man and machine.
    def parietal(self, currenttime):

        # This should really just be an addlive. Maybe
        # the other two functions, too.
        calendar = datetime.now(timezone(TIMEZONE))
        if calendar.hour in MEETUP_NOTIFY and 'peeps' in self.brainmeats:
            self.brainmeats['peeps'].meetup(calendar.hour)

        if currenttime - self.namecheck > 60:
            self.namecheck = int(mktime(localtime()))
            self.getnames()

        if currenttime - self.boredom > PATIENCE:
            self.boredom = int(mktime(localtime()))
            if randint(1, 10) == 7:
                self.bored()

        for func in self.live:
            self.live[func]()

    # And this is basic function that runs all the time.
    # The razor qualia edge of consciousness, if you will
    # (though you shouldn't). It susses out the important
    # info, logs the chat, sends PONG, finds commands, and
    # decides whether to send new information to the parser.
    def monitor(self):
        currenttime = int(mktime(localtime()))
        self.parietal(currenttime)

        self.sock.setblocking(0)
        try:
            lines = self.sock.recv(256)
        except:
            return

        for line in lines.split('\n'):
            line = line.strip()

            if re.search('^:' + NICK + '!~' + REALNAME + '@.+ JOIN ' + CHANNEL + '$', line):
                print "* Joined " + CHANNEL
                self.getnames()

            if self.gettingnames:
                if line.find('@ ' + CHANNEL) != -1:
                    all = line.split(':')[2]
                    self.gettingnames = False
                    all = re.sub(NICK + ' ', '', all)
                    self.members += list(set(all.split()) - set(self.members))

            scan = re.search(SCAN, line)
            ping = re.search('^PING', line)
            pwd = re.search(':-passwd', line)
            if line != '' and not scan and not ping and not pwd:
                self.logit(line + '\n')

            if line.find('PING') != -1:
                self.sock.send('PONG ' + line.split()[1] + '\n')
            elif line.find('PRIVMSG') != -1:
                self.boredom = currenttime
                content = line.split(' ', 3)
                self.context = content[2]

                if self.context == NICK:
                    self.lastprivate = content
                else:
                    self.lastpublic = content

                self.parse(line)

    # Le parser. This used to be a very busy function before
    # most of its actions got moved to the nonsense and 
    # broca brainmeats.
    def parse(self, msg):
        pwd = re.search(':-passwd', msg)
        if not pwd:
            print msg

        try:
            info, content = msg[1:].split(' :', 1)
            sender, type, room = info.strip().split()
        except:
            return

        try:
            nick, data = sender.split('!')
            realname, ip = data.split('@')
            ip = socket.gethostbyname_ex(ip.strip())[2][0]
            realname = realname[1:]
            self.lastrealsender = '%s@%s' % (realname, ip)
        except:
            return

        if nick not in self.members:
            self.members.append(nick)

        self.lastsender = nick
        self.lastip = ip

        # Determine if the action is a command and the user is
        # approved.
        if content[:1] == CONTROL_KEY:
            
            # Tack on last command if it's just the control
            if content == CONTROL_KEY or content[:2] == CONTROL_KEY + ' ':
                if not self.lastcommand:
                    return

                content = '%s%s %s' % (CONTROL_KEY, self.lastcommand, content[2:])

            if self.lastrealsender not in self.REALUSERS \
            and content[1:].split()[0] not in self.public_commands \
            and nick not in self.guests:
                self.chat('My daddy says not to listen to you.')
                return
            
            self.command(nick, content)
            return

        # This is a special case for giving people meaningless
        # points so you can feel like you're in grade school
        # again.
        if content[:-2] in self.members and content[-2:] in ['--', '++']:
            self.values = [content[:-2]]
            if content[-2:] == '++':
                self.chat(self.commands.get('increment')())
            if content[-2:] == '--':
                self.chat(self.commands.get('decrement')())
            return

        # Grab urls. Mongo automatically tries to get the title
        # and create a short link.
        ur = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        match_urls = re.compile(ur)
        urls = match_urls.findall(content)
        if len(urls):
            self.linker(urls)
            return

        # Been messing around with NLTK without much success,
        # but there's a lot of experimenting in the broca 
        # meat. At time of writing, it does Mongo's auto responses
        # in tourettes and adds to the markov chain.
        if 'broca' in self.brainmeats:
            self.brainmeats['broca'].tourettes(content, nick)
            self.brainmeats['broca'].mark(content)
            if self.autobabble and content.find(NICK) > 0:
                self.brainmeats['broca'].babble()

    # If it is indeed a command, the cortex stores who sent it,
    # and any words after the command are split in a values array,
    # accessible by the brainmeats as self.values.
    def command(self, sender, cmd):
        chain = cmd.split('|', 1)
        pipe = False

        if len(chain) is 2:
            cmd = chain[0].strip()
            pipe = chain[1].strip()

        components = cmd.split()
        what = components.pop(0)[1:]

        is_nums = re.search("^[0-9]+", what)
        is_breaky = re.search("^" + CONTROL_KEY + "|[^\w]+", what)
        if is_nums or is_breaky or not what:
            return

        if components:
            self.values = components
        else:
            self.values = False

        self.logit('%s sent command: %s\n' % (sender, what))
        self.lastsender = sender
        self.lastcommand = what

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
        # -tweet|babble or something."
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
        result = self.commands.get(what, self.default)()

        if not result:
            return

        if pipe:
            self.command(sender, '%s %s' % (pipe, result))
            return

        if type(result) in [str, unicode]:
            self.chat(result)

        if type(result) is list:
            for line in result:
                self.chat(line)

    # If you want to restrict a command to the bot admin.
    def validate(self):
        if not self.values:
            return False
        if self.lastsender != OWNER:
            return False
        return True

    # See who's about.
    def getnames(self):
        self.gettingnames = True
        self.sock.send('NAMES %s\n' % CHANNEL)

    # Careful with this one.
    def bored(self):
        if not self.members:
            return

        self.announce('Chirp chirp. Chirp Chirp.')

        # The behavior below is known to be highly obnoxious
        # self.act("is bored.")
        # self.act(choice(BOREDOM) + " " + choice(self.members))

    # Simple logging.
    def logit(self, what):
        with open(LOG, 'a') as f:
            f.write('TS:%s;%s' % (time.time(), what))

        now = date.today()
        if now.day != 1:
            return

        prev = date.today() - timedelta(days=1)
        backlog = '%s/%s-mongo.log' % (LOGDIR, prev.strftime('%Y%m'))
        if os.path.isfile(backlog):
            return

        shutil.move(LOG, backlog)

    # Sort out urls.
    def linker(self, urls):
        for url in urls:
            # Special behaviour for Twitter URLs
            match_twitter_urls = re.compile('http[s]?://(www.)?twitter.com/.+/status/([0-9]+)')

            twitter_urls = match_twitter_urls.findall(url)
            if len(twitter_urls):
                self.tweet(twitter_urls)
                return

            if url.find('gist.github') != -1:
                return

            if randint(1, 5) == 1:
                try:
                    self.commands.get('tweet', self.default)(url)
                except:
                    pass

            fubs = 0
            title = "Couldn't get title"

            site = Browse(url)

            if site.error:
                self.chat('Total fail: %s' % site.error)
                continue

            roasted = shorten(url)
            if not roasted:
                roasted = "Couldn't roast"
                fubs += 1

            try:
                ext = site.headers()['content-type'].split('/')[1]
            except:
                ext = False

            images = [
                'gif',
                'png',
                'jpg',
                'jpeg',
            ]

            if ext in images:
                title = 'Image'
                # Switch this to a Browse method
                #if STORE_IMGS:
                #    fname = url.split('/').pop()
                #    path = IMGS + fname
                #    savefromweb(url, path)

            elif ext == 'pdf':
                title = 'PDF Document'

            else:
                title = site.title()

            # If you have a delicious account set up. Yes, delicious
            # still exists. Could be updated to a cooler link 
            # collecting service.
            if STORE_URLS:
                postdelicious(url, title, self.lastsender)

            if fubs == 2:
                self.chat("Total fail")
            else:
                self.chat("%s @ %s" % (unescape(title), roasted))

    # This shows tweet content if a url is to a tweet.
    def tweet(self, urls):
        if 'twitting' not in self.brainmeats:
            return

        for url in urls:
            self.chat(self.brainmeats['twitting'].get_tweet(url[1]))

    # Announce means the chat is always sent to the channel,
    # never back as a private response.
    @ratelimited(2)
    def announce(self, message):
        self.chat(message, target=CHANNEL)

    # Since chat is mongo's only means of communicating with
    # a room, the ratelimiting here should prevent any overflow
    # violations.
    @ratelimited(2)
    def chat(self, message, target=False, error=False):
        if target:
            whom = target
        elif self.context == CHANNEL:
            whom = CHANNEL
        else:
            whom = self.lastsender

        filter(lambda x: x in string.printable, message)
        try:
            message = message.encode('utf-8')
            self.logit('___%s: %s\n' % (NICK, str(message)))
            m = str(message)
            if randint(1, 170) == 23:
                i = m.split()
                pos = randint(0, len(i))
                i.insert(pos, 'fnord')
                m = ' '.join(i)

            if error:
                m += ' ' + str(error)
            self.sock.send('PRIVMSG %s :%s\n' % (whom,m))
            if self.replysms:
                to = self.replysms
                self.replysms = False
                self.values = [to, str(m)]
                self.commands.get('sms')()
        except:
            self.sock.send('PRIVMSG %s :Having trouble saying that for some reason\n' % whom)

    def act(self, message, public=False, target=False):
        message = '\001ACTION %s\001' % message
        if public:
            self.announce(message)
        elif target:
            self.chat(message, target)
        else:
            self.chat(message)
            if self.replysms:
                to = self.replysms
                self.replysms = False
                self.values = [to, str(message)]
                self.commands.get('sms')()

    # When all else fails.
    def default(self):
        self.act(" cannot do this thing :'(")
