import os
import re
import shutil
import pkgutil
import requests

from bs4 import BeautifulSoup as bs4
from datetime import date, timedelta
from time import mktime, localtime, sleep
from random import randint

from settings import SAFE, NICK, CONTROL_KEY, LOG, LOGDIR, PATIENCE, \
    OWNER, REALNAME, SCAN
from secrets import CHANNEL, DELICIOUS_PASS, DELICIOUS_USER, USERS
from datastore import Drinker, connectdb
from util import unescape, pageopen, shorten, RateLimited
from autonomic import serotonin


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

        if self.gettingnames:
            if line.find("* " + CHANNEL) != -1:
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

    def showlist(self):
        if not self.values or self.values[0] not in self.helpmenu:
            cats = ", ".join(self.helpcategories)
            self.chat(CONTROL_KEY + "help WHAT where WHAT is " + cats)
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
        with open(LOG, 'a') as f:
            f.write(what)

        now = date.today()
        if now.day != 1:
            return

        prev = date.today() - timedelta(days=1)
        backlog = LOGDIR + "/" + prev.strftime("%Y%m") + "-mongo.log"
        if os.path.isfile(backlog):
            return

        shutil.move(LOG, backlog)

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
            realname = realname[1:]
        except:
            return

        self.lastsender = nick
        self.lastip = ip

        if content[:1] == CONTROL_KEY:
            if nick.rstrip('_') not in USERS:
                self.chat("My daddy says not to listen to you.")
                return

            self.command(nick, content)
            return

        if content[:-2] in USERS and content[-2:] in ['--', '++']:
            print "Active"
            self.values = [content[:-2]]
            if content[-2:] == '++':
                self.commands.get('increment')()
            if content[-2:] == '--':
                self.commands.get('decrement')()
            return

        ur = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        match_urls = re.compile(ur)
        urls = match_urls.findall(content)
        if len(urls):
            self.linker(urls)
            return

        if 'broca' in self.brainmeats:
            self.brainmeats['broca'].parse(content, nick)
            self.brainmeats['broca'].tourettes(content, nick)
            self.brainmeats['broca'].mark(content)

    def tweet(self, urls):
        # This should somehow call twitterapi.get_tweet
        for url in urls:
            response = pageopen('https://api.twitter.com/1.1/statuses/show.json?id=%s' % url[1])
            if not response:
                self.chat("Couldn't retrieve Tweet.")
                return

            try:
                json = response.json()
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

            if url.find('gist.github') != -1:
                return

            if randint(1, 5) == 1:
                self.commands.get("tweet", self.default)(url)

            while True:
                fubs = 0
                title = "Couldn't get title"
                roasted = "Couldn't roast"

                urlbase = pageopen(url)
                if not urlbase:
                    # we don't have a valid requests object here
                    # just give up early
                    self.chat("Total fail")
                    return

                try:
                    roasted = shorten(url)
                except:
                    fubs += 1

                ext = urlbase.headers['content-type'].split('/')[1]
                images = [
                    "gif",
                    "png",
                    "jpg",
                    "jpeg",
                ]

                if ext in images:
                    title = "Image"
                    break
                elif ext == "pdf":
                    title = "PDF Document"
                    break
                else:
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

            print "Delic"
            deli = "https://api.del.icio.us/v1/posts/add"
            params = {
                "url": url,
                "description": title,
                "tags": "okdrink," + self.lastsender,
            }

            if DELICIOUS_USER:
                auth = requests.auth.HTTPBasicAuth(DELICIOUS_USER, DELICIOUS_PASS)
                try:
                    send = requests.get(deli, params=params, auth=auth)
                except:
                    self.chat("(delicious is down)")

                if not send:
                    self.chat("(delicious problem)")

            if fubs == 2:
                self.chat("Total fail")
            else:
                self.chat(unescape(title) + " @ " + roasted)

            print "All the way"
            break

    def announce(self, message, whom=False):
        message = message.encode("utf-8")
        try:
            self.sock.send('PRIVMSG ' + CHANNEL + ' :' + str(message) + '\n')
        except:
            self.sock.send('PRIVMSG ' + CHANNEL + ' :Having trouble saying that for some reason\n')

    @RateLimited(5)
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

    def default(self):
        self.act(" cannot do this thing :'(")
