#System

import base64
import string
import os
import re
import urllib2
import urllib
import simplejson
import shutil
import settings 

from BeautifulSoup import BeautifulSoup as soup
from datetime import date, timedelta
from time import mktime, localtime, sleep
from random import choice, randint

# Local
from settings import SAFE, NICK, CONTROL_KEY, LOG, LOGDIR, PATIENCE, \
                     ACROSCORE, CHANNEL, SHORTENER, OWNER
from secrets import DELICIOUS_PASS, DELICIOUS_USER
from datastore import Drinker, connectdb
from util import unescape, pageopen
from autonomic import serotonin
from acro import Acro
from holdem import Holdem

# TODO: standardize url grabber
# TODO: move out live responses to something?

class Cortex:
    def __init__(self, master):
        self.acro = False
        self.playingholdem = False
        self.values = False
        self.master = master
        self.context = CHANNEL
        self.sock = master.sock
        self.gettingnames = True
        self.members = []
        self.memories = False
        self.boredom = int(mktime(localtime()))
        self.namecheck = int(mktime(localtime()))
        self.safe_calc = dict([(k, locals().get(k, f)) for k, f in SAFE])
        self.holdem = Holdem(self)

        self.helpmenu = { 
            "h":[
                "~holdem <start holdem game>",
                "~bet [amount] <>",
                "~call <match bet, if able>",
                "~raise [amount] <raise the bet>",
                "~pass/~knock/~check  <pass bet>",
                "~fold <leave hand>",
                "~allin <bet everything>",
                "~sitout <leave game temporarily>",
                "~sitin <rejoin game>",
                "~status <show all players' money and status>",
                "~pot <show amount in pot>",
                "~mymoney <show how much money you have>",
                "~thebet <show current bet>",
            ],
            "a":[
                "~roque/~acro [pause|resume|end] <start acro game>",
                "~rules <print the rules for the acro game>",
                "~boards <show cumulative acro game scores>",
            ],
        }

        self.commands = {
            # Help menu 
            "help": self.showlist,

            # Acro
            "roque": self.acroengine,
            "acro": self.acroengine,
            "boards": self.boards,
            "rules": self.rules,

            # Holdem
            "holdem": self.holdemengine,
            "bet": self.holdem.raiseit,
            "call": self.holdem.callit,
            "raise": self.holdem.raiseit,
            "pass": self.holdem.knock,
            "knock": self.holdem.knock,
            "check": self.holdem.knock,
            "fold": self.holdem.fold,
            "allin": self.holdem.allin,
            "sitin": self.holdem.sitin,
            "sitout": self.holdem.sitout,
            "status": self.holdem.status,
            "pot": self.holdem.showpot,
            "mymoney": self.holdem.mymoney,
            "thebet": self.holdem.thebet,
        }
        
        self.helpcategories = [
            "(a)cro", 
            "(h)oldem", 
        ] 

        self.loadbrains()

        connectdb()

    def loadbrains(self, electroshock = False):

        areas = [
            "chess",
            "finance",
            "memory",
            "nonsense",
            "peeps",
            "management",
            "broca",
            "reference",
            "system",
        ]

        self.brainmeats = {}

        for area in areas:
            mod = __import__(area, fromlist = [])
            if electroshock:
                reload(mod)
            cls = getattr(mod, area.capitalize())
            self.brainmeats[area] = cls(self)

        for brainmeat in self.brainmeats:
            serotonin(self, self.brainmeats[brainmeat])

    def monitor(self, sock):
        line = self.sock.recv(500)
        line = line.strip()

        currenttime = int(mktime(localtime()))
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
            self.boredom = int(mktime(localtime()))
            content = line.split(' ', 3)
            self.context = content[2]

            if self.acro and line.find(CONTROL_KEY) == -1:
                if self.context == NICK:
                    self.acro.input(content)

            self.parse(line)

        if currenttime - self.namecheck > 300:
            self.namecheck = int(mktime(localtime()))
            self.getnames()

        if currenttime - self.boredom > PATIENCE:
            self.boredom = int(mktime(localtime()))
            if randint(1, 10) == 7:
                self.bored()

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

    # TODO: still broken
    def reload(self):
        return

    def showlist(self):
        if not self.values or self.values[0] not in self.helpmenu: 
            self.chat("Use " + CONTROL_KEY + "help [what] where what is " + ", ".join(self.helpcategories))
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
        info, content = msg[1:].split(' :', 1)
        try:
            sender, type, room = info.strip().split()
        except:
            return

        try:
            nick = sender.split('!')[0]
            ip = sender.split('@')[1]
        except:
            return

        self.lastsender = nick

        if content[:1] == CONTROL_KEY:
            self.command(nick, content)
            return

        match_urls = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = match_urls.findall(content)
        if len(urls):
            self.linker(urls)
            return

        # TODO: figure this out
        # self.broca.parse(content)

        if content.find(NICK + " sucks") != -1:
            self.chat(nick + "'s MOM sucks")
            return

        if "mom" in content.translate(string.maketrans("", ""), string.punctuation).split():
            open(LOGDIR + "/mom.log", 'a').write(content + '\n')
            return

        if content.lower().find("oh snap") != -1:
            self.chat("yeah WHAT?? Oh yes he DID")
            return

        if content.lower().find("rimshot") != -1:
            self.chat("*ting*")
            return

        if content.lower().find("stop") == len(content) - 4 and len(content) != 3:
            self.chat("Hammertime")
            return

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

            # TODO make this better
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
        # TODO: why is this commented?
        #message = self.colortext(message)
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


    # Not necessary to keep in cortex, to be moved out

    def rules(self):
        self.chat("1 of 6 start game with ~roque.")
        self.chat("2 of 6 when the acronym comes up, type /msg " + NICK + " your version of what the acronym stands for.")
        self.chat("3 of 6 each word of your submission is automatically updated unless you preface it with '-', so 'do -it up' will show as 'Do it Up'.")
        self.chat("4 of 6 when the voting comes up, msg " + NICK + " with the number of your vote.")
        self.chat("5 of 6 play till the rounds are up.")
        self.chat("6 of 6 " + NICK + " plays by default. Run ~update BOTPLAY False to turn it off.")

    # TODO: put this in acro.py
    def boards(self):
        scores = {}

        for path, dirs, files in os.walk(os.path.abspath(ACROSCORE)):
            for file in files:
                for line in open(path + "/" + file):
                    if line.find(":") == -1:
                        try:
                            player, score, toss = line.split()
                            if player in scores:
                                scores[player]['score'] += int(score)
                                scores[player]['rounds'] += 1
                            else:
                                scores[player] = {'score': int(score), 'rounds': 1}
                        except:
                            continue

        for player in scores:
            score = scores[player]['score']
            average = score / scores[player]['rounds']

            self.chat(player + ": " + str(score) + " (" + str(average) + " per round)")

    def holdemengine(self):
        if self.playingholdem:
            self.chat("Already a game in progress")
            return

        self.playingholdem = True
        self.holdem.start()

    def acroengine(self):

        if self.acro:
            if self.values:
                action = self.values[0]
                if action == "pause":
                    if self.acro.wait:
                        self.acro.paused = True
                        self.announce("Game paused")
                    else:
                        self.chat("You can only pause between rounds.")

                elif action == "resume":
                    self.acro.paused = False
                    self.announce("Game on")
                elif action == "end":
                    self.acro.killgame = True
                else:
                    self.chat("Not a valid action")

                return

            self.chat("Already a game in progress")
            return

        self.acro = Acro(self)
        self.acro.start()

