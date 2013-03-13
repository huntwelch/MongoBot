#System

import base64
import os
import re
import urllib2
import urllib
import simplejson
import shutil
import pkgutil

from BeautifulSoup import BeautifulSoup as soup
from datetime import date, timedelta
from time import mktime, localtime, sleep
from random import choice, randint

# Local
from settings import SAFE, NICK, CONTROL_KEY, LOG, LOGDIR, PATIENCE, \
    ACROSCORE, CHANNEL, SHORTENER, OWNER, REALNAME, BANNED, USERS
from secrets import DELICIOUS_PASS, DELICIOUS_USER
from datastore import Drinker, connectdb
from util import unescape, pageopen
from autonomic import serotonin


class Cortex:
    def __init__(self, master):
        
        print "* Initializing"
        self.values = False
        self.master = master
        self.context = CHANNEL
        self.lastpublic = False 
        self.lastprivate = False 
        self.sock = master.sock
        self.gettingnames = True
        self.members = []
        self.memories = False
        self.boredom = int(mktime(localtime()))
        self.namecheck = int(mktime(localtime()))
        self.live = {}

        self.helpmenu = {}
        self.commands = {
            "help": self.showlist,
        }
        self.helpcategories = []

        print "* Loading brainmeats"
        self.loadbrains()

        print "* Connecting to datastore"
        connectdb()

    def loadbrains(self, electroshock=False):
        self.brainmeats = {}
        brainmeats = __import__("brainmeats", fromlist=[])
        if electroshock:
            reload(brainmeats)

        areas = [name for _, name, _ in pkgutil.iter_modules(['brainmeats'])]

        for area in areas:
            mod = __import__("brainmeats", fromlist=[area])
            mod = getattr(mod, area)
            if electroshock:
                reload(mod)
            cls = getattr(mod, area.capitalize())
            self.brainmeats[area] = cls(self)

        for brainmeat in self.brainmeats:
            serotonin(self, self.brainmeats[brainmeat], electroshock)

    def addlive(self, func):
        self.live[func.__name__] = func

    def droplive(self, name):
        self.live[name] = False

    def parietal(self, currenttime):
        if currenttime - self.namecheck > 300:
            self.namecheck = int(mktime(localtime()))
            self.getnames()

        if currenttime - self.boredom > PATIENCE:
            self.boredom = int(mktime(localtime()))
            if randint(1, 10) == 7:
                self.bored()

        for func in self.live:
            if self.live[func]:
                self.live[func]()

    def monitor(self, sock):
        currenttime = int(mktime(localtime()))
        self.parietal(currenttime)

        try:
            line = self.sock.recv(500)
        except:
            return

        line = line.strip()
        
        if re.search("^:" + NICK + "!~" + REALNAME + "@.+ JOIN " + CHANNEL + "$", line):
            print "* Joined " + CHANNEL

        # TODO: build scan check from settings
        scan = re.search("^:\w+\.freenode\.net", line)
        ping = re.search("^PING", line)
        if line != '' and not scan and not ping:
            self.logit(line + '\n')

        if self.gettingnames:
            if line.find("* " + CHANNEL) != -1:
                all = line.split(":")[2]
                self.gettingnames = False
                all = re.sub(NICK + ' ', '', all)
                self.members = all.split()

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

    def command(self, sender, cmd):
        components = cmd.split()
        what = components.pop(0)[1:]

        is_nums = re.search("^[0-9]+", what)
        is_breaky = re.search("^" + CONTROL_KEY + "+", what)
        if is_nums or is_breaky:
            return

        if components:
            self.values = components
        else:
            self.values = False

        self.logit(sender + " sent command: " + what + "\n")
        self.lastsender = sender
        self.lastcommand = what

        self.commands.get(what, self.default)()

    def showlist(self):
        if not self.values or self.values[0] not in self.helpmenu:
            cats = ", ".join(self.helpcategories)
            self.chat(CONTROL_KEY + "help [what] where what is " + cats)
            return

        which = self.values[0]

        for command in self.helpmenu[which]:
            sleep(1)
            self.chat(command)

    def validate(self):
        if not self.values:
            return False
        if self.lastsender != OWNER:
            return False
        return True

    def getnames(self):
        self.gettingnames = True
        self.sock.send('NAMES ' + CHANNEL + '\n')

    def bored(self):
        if not self.members:
            return

        self.announce("Chirp chirp. Chirp Chirp.")

        # The behavior below is known to be highly obnoxious
        # self.act("is bored.")
        # self.act(choice(BOREDOM) + " " + choice(self.members))

    def logit(self, what):
        open(LOG, 'a').write(what)

        now = date.today()
        if now.day != 1:
            return

        prev = date.today() - timedelta(days=1)
        backlog = LOGDIR + "/" + prev.strftime("%Y%m") + "-mongo.log"
        if os.path.isfile(backlog):
            return

        shutil.move(LOG, backlog)

    def parse(self, msg):

        print msg

        info, content = msg[1:].split(' :', 1)
        try:
            sender, type, room = info.strip().split()
        except:
            return

        try:
            nick, data = sender.split('!')
            realname, ip = data.split('@')
            realname = realname[1:]
        except:
            return

        if nick in BANNED:
            return

        if nick not in USERS:
            return

        self.lastsender = nick

        if content[:1] == CONTROL_KEY:
            self.command(nick, content)
            return

        ur = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        match_urls = re.compile(ur)
        urls = match_urls.findall(content)
        if len(urls):
            self.linker(urls)
            return

        self.brainmeats['broca'].parse(content, nick)
        self.brainmeats['broca'].tourettes(content, nick)

    def tweet(self, urls):
        for url in urls:
            response = pageopen('https://api.twitter.com/1/statuses/show.json?id=%s' % url[1])
            if not response:
                self.chat("Couldn't retrieve Tweet.")
                return

            try:
                json = simplejson.loads(response)
            except:
                self.chat("Couldn't parse Tweet.")
                return

            name = json['user']['name']
            screen_name = json['user']['screen_name']
            text = json['text']

            self.chat('%s (%s) tweeted: %s' % (name, screen_name, text))

    def linker(self, urls):
        for url in urls:
            # Special behaviour for Twitter URLs
            match_twitter_urls = re.compile('http[s]?://(www.)?twitter.com/.+/status/([0-9]+)')

            twitter_urls = match_twitter_urls.findall(url)
            if len(twitter_urls):
                self.tweet(twitter_urls)
                return

            fubs = 0
            title = "Couldn't get title"
            roasted = "Couldn't roast"

            urlbase = pageopen(url)
            if not urlbase:
                fubs += 1

            try:
                opener = urllib2.build_opener()
                roasted = opener.open(SHORTENER + url).read()
            except:
                fubs += 1

            ext = url.split(".")[-1]
            images = [
                "gif",
                "png",
                "jpg",
                "jpeg",
            ]

            if ext in images:
                title = "Image"
            elif ext == "pdf":
                title = "PDF Document"
            else:
                try:
                    cont = soup(urlbase)
                    title = cont.title.string
                except:
                    self.chat("Page parsing error")
                    return

            deli = "https://api.del.icio.us/v1/posts/add?"
            data = urllib.urlencode({
                "url": url,
                "description": title,
                "tags": "okdrink," + self.lastsender,
            })
            base64string = base64.encodestring('%s:%s' % (DELICIOUS_USER, DELICIOUS_PASS))[:-1]

            try:
                req = urllib2.Request(deli, data)
                req.add_header("Authorization", "Basic %s" % base64string)
                send = urllib2.urlopen(req)
            except:
                self.chat("(delicious is down)")

            if fubs == 2:
                self.chat("Total fail")
            else:
                self.chat(unescape(title) + " @ " + roasted)

    def announce(self, message, whom=False):
        message = message.encode("utf-8")
        try:
            self.sock.send('PRIVMSG ' + CHANNEL + ' :' + str(message) + '\n')
        except:
            self.sock.send('PRIVMSG ' + CHANNEL + ' :Having trouble saying that for some reason\n')

    def chat(self, message, target=False):
        if target:
            whom = target
        elif self.context == CHANNEL:
            whom = CHANNEL
        else:
            whom = self.lastsender
        message = message.encode("utf-8")
        try:
            self.sock.send('PRIVMSG ' + whom + ' :' + str(message) + '\n')
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

    def default(self):
        self.chat(NICK + " cannot do this thing :'(")
