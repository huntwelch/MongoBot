import os
import re
import shutil
import pkgutil
import requests
import thread
import socket
import time

from bs4 import BeautifulSoup as bs4
from datetime import date, timedelta
from time import mktime, localtime, sleep
from random import randint

from settings import SAFE, NICK, CONTROL_KEY, LOG, LOGDIR, PATIENCE, SCAN, STORE_URLS, STORE_IMGS, IMGS, REGISTERED 
from secrets import CHANNEL, OWNER, REALNAME
from datastore import Drinker, connectdb
from util import unescape, pageopen, shorten, ratelimited, postdelicious, savefromweb
from autonomic import serotonin

# Basically all the interesting interaction with
# irc and command / content parsing happens here.
# Also connects to mongodb.
class Cortex:
    def __init__(self, master):

        print "* Initializing"
        self.values = False
        self.master = master
        self.context = CHANNEL
        self.lastpublic = False
        self.replysms = False
        self.lastprivate = False
        self.lastsender = False
        self.sock = master.sock
        self.gettingnames = True
        self.members = []
        self.guests = [] 
        self.memories = False
        self.autobabble = False
        self.boredom = int(mktime(localtime()))
        self.namecheck = int(mktime(localtime()))
        self.live = {}
        self.public_commands = []

        self.helpmenu = {}
        self.commands = {
            "help": self.showlist,
        }
        self.helpcategories = []

        print "* Loading brainmeats"
        self.loadbrains()

        print "* Loading users"
        users = open(REGISTERED, 'r')
        self.REALUSERS = users.read().splitlines()
        users.close()

        print "* Connecting to datastore"
        connectdb()

    # Loads up all the files in brainmeats and runs them 
    # through the hookup process.
    def loadbrains(self, electroshock=False):
        self.brainmeats = {}
        brainmeats = __import__("brainmeats", fromlist=[])
        if electroshock:
            reload(brainmeats)

        areas = [name for _, name, _ in pkgutil.iter_modules(['brainmeats'])]

        for area in areas:
            if area not in self.master.ENABLED:
                continue

            print area
            try:
                mod = __import__("brainmeats", fromlist=[area])
                mod = getattr(mod, area)
                if electroshock:
                    reload(mod)
                cls = getattr(mod, area.capitalize())
                self.brainmeats[area] = cls(self)
            except Exception as e:
                self.chat("Failed to load " + area + ".")
                print "Failed to load " + area + "."
                print e

        for brainmeat in self.brainmeats:
            serotonin(self, self.brainmeats[brainmeat], electroshock)

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
    def addlive(self, func):
        self.live[func.__name__] = func

    def droplive(self, name):
        self.live[name] = False

    # Core automatic stuff. I firmly believe boredom to
    # be a fundamental process in both man and machine.
    def parietal(self, currenttime):
        if currenttime - self.namecheck > 60:
            self.namecheck = int(mktime(localtime()))
            self.getnames()

        if currenttime - self.boredom > PATIENCE:
            self.boredom = int(mktime(localtime()))
            if randint(1, 10) == 7:
                self.bored()

        for func in self.live:
            if self.live[func]:
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

        for line in lines.split("\n"):
            line = line.strip()

            if re.search("^:" + NICK + "!~" + REALNAME + "@.+ JOIN " + CHANNEL + "$", line):
                print "* Joined " + CHANNEL
                self.getnames()

            if self.gettingnames:
                if line.find("@ " + CHANNEL) != -1:
                    all = line.split(":")[2]
                    self.gettingnames = False
                    all = re.sub(NICK + ' ', '', all)
                    self.members = all.split()

            scan = re.search(SCAN, line)
            ping = re.search("^PING", line)
            pwd = re.search(":-passwd", line)
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
        pwd = re.search(":-passwd", msg)
        if not pwd:
            print msg

        info, content = msg[1:].split(' :', 1)
        try:
            sender, type, room = info.strip().split()
        except:
            return

        try:
            nick, data = sender.split('!')
            realname, ip = data.split('@')
            ip = socket.gethostbyname_ex(ip.strip())[2][0]
            realname = realname[1:]
            self.lastrealsender = "%s@%s" % (realname, ip)
        except:
            return

        self.lastsender = nick
        self.lastip = ip

        # Determine if the action is a command and the user is
        # approved.
        if content[:1] == CONTROL_KEY:
            if self.lastrealsender not in self.REALUSERS and content[1:].split()[0] not in self.public_commands and nick not in self.guests:
                self.chat("My daddy says not to listen to you.")
                return
            
            print "Executing command: %s" % content
            _mark = int(mktime(localtime()))
            self.command(nick, content)
            print "Finished in: %s" % str(int(mktime(localtime())) - _mark)
            return

        # This is a special case for giving people meaningless
        # points so you can feel like you're in grade school
        # again.
        if content[:-2] in self.members and content[-2:] in ['--', '++']:
            print "Active"
            self.values = [content[:-2]]
            if content[-2:] == '++':
                self.commands.get('increment')()
            if content[-2:] == '--':
                self.commands.get('decrement')()
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

        self.logit(sender + " sent command: " + what + "\n")
        self.lastsender = sender
        self.lastcommand = what

        self.commands.get(what, self.default)()

    # Help menu. It used to just show every command, but there
    # are so goddamn many at this point, they had to be split
    # into categories.
    def showlist(self):
        if not self.values or self.values[0] not in self.helpmenu:
            cats = ", ".join(self.helpcategories)
            self.chat(CONTROL_KEY + "help WHAT where WHAT is " + cats)
            return

        which = self.values[0]

        for command in self.helpmenu[which]:
            sleep(1)
            self.chat(command)

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
        self.sock.send('NAMES ' + CHANNEL + '\n')

    # Careful with this one.
    def bored(self):
        if not self.members:
            return

        self.announce("Chirp chirp. Chirp Chirp.")

        # The behavior below is known to be highly obnoxious
        # self.act("is bored.")
        # self.act(choice(BOREDOM) + " " + choice(self.members))

    # Simple logging.
    def logit(self, what):
        with open(LOG, 'a') as f:
            f.write("TS:%s;%s" % (time.time(), what))

        now = date.today()
        if now.day != 1:
            return

        prev = date.today() - timedelta(days=1)
        backlog = LOGDIR + "/" + prev.strftime("%Y%m") + "-mongo.log"
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
                    self.commands.get("tweet", self.default)(url)
                except:
                    pass

            while True:
                fubs = 0
                title = "Couldn't get title"
                roasted = "Couldn't roast"

                urlbase = pageopen(url)
                if not urlbase:
                    # If we don't have a valid requests
                    # object here just give up early
                    self.chat("Total fail")
                    return

                roasted = shorten(url)
                if not roasted:
                    roasted = ''
                    fubs += 1

                try:
                    ext = urlbase.headers['content-type'].split('/')[1]
                except:
                    ext = False

                images = [
                    "gif",
                    "png",
                    "jpg",
                    "jpeg",
                ]

                if ext in images:
                    title = "Image"
                    if STORE_IMGS:
                        # This needs to be threaded. Cause images can be 
                        # big n stuff.
                        fname = url.split('/').pop()
                        path = IMGS + fname
                        thread.start_new_thread(savefromweb, (url, path))
                    break
                elif ext == "pdf":
                    title = "PDF Document"
                    break
                else:
                    # Bit of ugliness here.
                    try:
                        soup = bs4(urlbase.text)
                        title = soup.find('title').string.strip()
                        if title is None:
                            redirect = soup.find('meta', attrs={'http-equiv':
                                                 'refresh'})
                            if not redirect:
                                redirect = soup.find('meta', attrs={'http-equiv':
                                                     'Refresh'})

                            if redirect:
                                # Shouldn't this call itself and then return here?
                                url = redirect['content'].split('url=')[1]
                                continue
                            else:
                                raise ValueError('Cannot find title')
                        break

                    except:
                        self.chat("Page parsing error - " + roasted)
                        return

            # If you have a delicious account set up. Yes, delicious
            # still exists. Could be updated to a cooler link 
            # collecting service.
            if STORE_URLS:
                postdelicious(url, title, self.lastsender)

            if fubs == 2:
                self.chat("Total fail")
            else:
                self.chat(unescape(title) + " @ " + roasted)

            break

    # This shows tweet content if a url is to a tweet.
    def tweet(self, urls):

        if 'twitterapi' not in self.brainmeats:
            return

        for url in urls:
            self.brainmeats['twitterapi'].get_tweet(url[1])

    # Announce means the chat is always sent to the channel,
    # never back as a private response.
    @ratelimited(2)
    def announce(self, message, whom=False):
        message = message.encode("utf-8")
        try:
            self.sock.send('PRIVMSG ' + CHANNEL + ' :' + str(message) + '\n')
        except:
            self.sock.send('PRIVMSG ' + CHANNEL + ' :Having trouble saying that for some reason\n')

    # Since chat is mongo's only means of communicating with
    # a room, the ratelimiting here should prevent any overflow
    # violations.
    @ratelimited(2)
    def chat(self, message, target=False):
        if target:
            whom = target
        elif self.context == CHANNEL:
            whom = CHANNEL
        else:
            whom = self.lastsender
        message = message.encode("utf-8")
        self.logit("___" + NICK + ": " + str(message) + '\n')
        try:
            self.sock.send('PRIVMSG ' + whom + ' :' + str(message) + '\n')
            if self.replysms:
                to = self.replysms
                self.replysms = False
                self.values = [to, str(message)]
                self.commands.get('sms')()
        except:
            self.sock.send('PRIVMSG ' + whom + ' :Having trouble saying that for some reason\n')

    def act(self, message, public=False, target=False):
        message = "\001ACTION " + message + "\001"
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
