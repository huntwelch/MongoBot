import base64
import string
import os
import re
import htmlentitydefs
import random
import urllib2
import urllib
import MySQLdb
import simplejson
import shutil

from datastore import Drinker, connectdb
from datetime import date, timedelta
from math import *
from time import *
from random import choice
from util import unescape
from autonomic import serotonin

from BeautifulSoup import BeautifulSoup as soup

import acro
import holdem
import redmine
import broca

from settings import *
from secrets import *
from acro import Acro
from holdem import Holdem
from redmine import Redmine
from broca import Broca
from chess import Chess
from finance import Finance 
from memory import Memory
from nonsense import Nonsense

# TODO: standardize url grabber


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
        self.redmine = Redmine(self)
        self.holdem = Holdem(self)
        self.broca = Broca(self)

        self.helpmenu = { 
            "g":[
                "~g [what]<search google>",
                "~love <command " + NICK + " to love>",
                "~hate <command " + NICK + " to hate>",
                "~settings <show current settings>",
                "~reload <reload libraries>",
                "~reboot <guess>",
                "~bored <make " + NICK + " bored>",
                "~update SETTING_NAME [value] <change a setting>",
                "~mom <randomly reprint a message containing 'mom'>",
                "~distaste <command " + NICK + " to express disastisfaction>",
                "~distaste [url] <expand " + NICK + "'s to disastisfaction repertoire>",
                "~intros <show history of " + CHANNEL + ">",
                "~source <link to repo for " + NICK + ">",
                "~workat <register what company you work at>",
                "~companies <show who works where>",
                "~company <show the company a specific person works for>",
                "~weather <get weather by zip code>",
            ],
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
                "~learnword someword <add a word to bot's acronym library>",
                "~boards <show cumulative acro game scores>",
            ],
            "l":[
                "~anagram [phrase] <get anagrams of phrase>",
                "~think [abc] <come up with an acronym for submitted letters>",
                "~ety <get etymology of word>",
                "~buzz <generate buzzword bullshit>",
                "~whatmean/~def [someword] <look up word in local database or wordnik>",
                "~calc <show available python math functions>",
                "~calc equation <run a simple calculation>",
            ],
            "r":[
                "~register [api key] <register your redmine api key with MongoBot>",
                "~hot <display all unassigned hotfixes>",
                "~detail [ticket number] <get a ticket description>",
                "~snag [ticket number] <assign a ticket to yourself>",
                "~assign [user nick] [ticket number] <assign a ticket to someone else>",
                "~tickets [user; optional] <show assigned tickets for user>",
            ],
        }

        self.commands = {
            # General
            "help": self.showlist,
            "settings": self.showsettings,
            "think": self.think,
            "learnword": self.learnword,
            "calc": self.calc,
            "bored": self.bored,
            "names": self.getnames,
            "g": self.goog,
            "ety": self.ety,
            "anagram": self.anagram,
            "intros": self.intros,
            "source": self.source,
            "workat": self.workat,
            "companies": self.companies,
            "company": self.company,
            "all": self.all,
            "weather": self.weather,

            # System
            "update": self.update,
            "reboot": self.master.die,
            "reload": self.master.reload,

            # Redmine
            "hot": self.redmine.showhotfix,
            "tickets": self.redmine.showtickets,
            "register": self.redmine.register,
            "assign": self.redmine.assignment,
            "snag": self.redmine.assignment,
            "detail": self.redmine.showdetail,

            # Language
            "whatmean": self.broca.whatmean,
            "def": self.broca.whatmean,
            "speak": self.broca.speak,

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
            "testcolor": self.testcolor,
        }
        
        self.helpcategories = [
            "(g)eneral", 
            "(l)anguage and math", 
            "(m)emory", 
            "(a)cro", 
            "(h)oldem", 
            "(r)edmine",
        ] 

        expansions = [
            Chess(self),
            Finance(self),
            Memory(self),
            Nonsense(self),
        ]

        for expansion in expansions:
            serotonin(self, expansion)

        connectdb()  

    # a lot of this doesn't seem to work :/
    def reload(self):
        reload(acro)
        reload(redmine)
        reload(broca)
        reload(holdem)
        reload(stocks)
        from acro import Acro
        from holdem import Holdem
        from redmine import Redmine
        from broca import Broca
        from stocks import Stock
        self.redmine = Redmine(self)
        self.holdem = Holdem(self)
        self.broca = Broca(self)

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

            # TODO: this check could be better
            if self.acro and line.find('~') == -1:
                if self.context == NICK:
                    self.acro.input(content)

            self.parse(line)

        if currenttime - self.namecheck > 300:
            self.namecheck = int(mktime(localtime()))
            self.getnames()

        if currenttime - self.boredom > PATIENCE:
            self.boredom = int(mktime(localtime()))
            if random.randint(1, 10) == 7:
                self.bored()

    def command(self, sender, cmd):
        components = cmd.split()
        what = components.pop(0)[1:]

        is_nums = re.search("^[0-9]+", what)
        is_breaky = re.search("^~+", what)
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
            self.chat("Use ~help [what] where what is " + ", ".join(self.helpcategories))
            return

        which = self.values[0]

        for command in self.helpmenu[which]:
            sleep(1)
            self.chat(command)

    def weather(self):
        if not self.values or not re.search("^\d{5}", self.values[0]): 
            self.chat("Please enter a zip code.")
            return
        
        zip = self.values[0]
        url = "http://api.wunderground.com/api/%s/conditions/q/%s.json" % (WEATHER_API, zip)
 
        response = self.pageopen(url)
        if not response:
            self.chat("Couldn't get weather.")
            return

        try:
            json = simplejson.loads(response)
        except:
            self.chat("Couldn't parse weather.")
            return
       
        json = json['current_observation']

        location = json['display_location']['full']
        condition = json['weather']
        temp = json['temperature_string']
        humid = json['relative_humidity']
        wind = json['wind_string']
        feels = json['feelslike_string']

        base = "%s, %s, %s, Humidity: %s, Wind: %s, Feels like: %s"
        self.chat( base % (location, condition, temp, humid, wind, feels) )

    def workat(self):
        if not self.values: 
            self.chat("If you're unemployed, that's cool, just don't abuse the bot")
            return
        
        name = self.lastsender  
        company = " ".join(self.values)

        drinker = Drinker.objects(name = name)
        if drinker:
            drinker = drinker[0]
            drinker.company = company
        else:
            drinker = Drinker(name = name, company = company) 

        drinker.save()

    def companies(self):
        for drinker in Drinker.objects:
            self.chat(drinker.name + ": " + drinker.company)

    def company(self):
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        user = Drinker.objects(name = search_for)[0]
        if user and user.company:
            self.chat(user.name + ": " + user.company)
        else:
            self.chat("Tell that deadbeat %s to get a damn job already..." % search_for)

    def source(self):
        self.chat(REPO)

    def intros(self):
        text = ""
        try:
            file = open(STORAGE + "/introductions")
        except:
            self.chat("No introductions file")
            return

        for line in file:
            if line.strip() == "---":
                self.chat(text)
                text = ""
                continue

            text += " " + line.strip()

        self.chat(text)

    def btc(self):
        url = 'https://mtgox.com/api/1/BTCUSD/ticker'

        response = self.pageopen(url)
        if not response:
            self.chat("Couldn't retrieve BTC data.")
            return

        try:
            json = simplejson.loads(response)
        except:
            self.chat("Couldn't parse BTC data.")
            return

        last = json['return']['last_all']['display_short']
        low = json['return']['low']['display_short']
        high = json['return']['high']['display_short']

        self.chat('Bitcoin, Last: %s, Low: %s, High: %s' % (last, low, high))        

    def testcolor(self):
        self.chat(u'\u2660' + "\x034" + u'\u2665' + u'\u2666' + "\x03" + u'\u2663')

    def goog(self):
        if not self.values:
            self.chat("Enter a word")
            return
        
        query = "+".join(self.values)
        url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=large&q=%s&start=0" % (query)

        # Google no likey pageopen func

        try: 
            results = urllib.urlopen(url)
            json = simplejson.loads(results.read())
        except:
            self.chat("Something's buggered up")
            return
        
        if json["responseStatus"] != 200:
            self.chat("Bad status")
            return

        result = json["responseData"]["results"][0]
        title = result["titleNoFormatting"]
        link = result["url"]

        self.chat(title + " @ " + link)

        return

    def ety(self):
        if not self.values:
            self.chat("Enter a word")
            return

        word = self.values[0]
        url = "http://www.etymonline.com/index.php?allowed_in_frame=0&search=" + word + "&searchmode=term"

        urlbase = self.pageopen(url)
        if not urlbase:
            self.chat("Couldn't find anything")
            return

        cont = soup(urlbase)

        heads = cont.findAll("dt")
        defs = cont.findAll("dd")

        if not len(defs):
            self.chat("Couldn't find anything")
            return

        try:
            ord = int(self.values[1])
        except:
            ord = 1

        if ord > len(defs):
            ord = 1

        ord -= 1
        if ord < 0:
            ord = 0

        _word = ''.join(heads[ord].findAll(text=True)).encode("utf-8")
        _def = ''.join(defs[ord].findAll(text=True)).encode("utf-8")

        self.chat("Etymology " + str(ord + 1) + " of " + str(len(defs)) +
                " for " + _word + ": " + _def)

    def anagram(self):
        if not self.values:
            self.chat("Enter a word or phrase")
            return

        word = '+'.join(self.values)
        url = "http://wordsmith.org/anagram/anagram.cgi?anagram=" + word + "&t=50&a=n"

        urlbase = self.pageopen(url)
        if not urlbase:
            self.chat("Couldn't find anything")
            return

        cont = soup(urlbase)

        paragraph = cont.findAll("p")[4]
        content = ''.join(paragraph.findAll()).replace("<br/>", ", ").encode("utf-8")
        self.chat(content)

    def validate(self):
        if not self.values:
            return False
        if self.lastsender != OWNER:
            return False

        return True

    def rules(self):
        self.chat("1 of 6 start game with ~roque.")
        self.chat("2 of 6 when the acronym comes up, type /msg " + NICK + " your version of what the acronym stands for.")
        self.chat("3 of 6 each word of your submission is automatically updated unless you preface it with '-', so 'do -it up' will show as 'Do it Up'.")
        self.chat("4 of 6 when the voting comes up, msg " + NICK + " with the number of your vote.")
        self.chat("5 of 6 play till the rounds are up.")
        self.chat("6 of 6 " + NICK + " plays by default. Run ~update BOTPLAY False to turn it off.")

    def getnames(self):
        self.gettingnames = True
        self.sock.send('NAMES ' + CHANNEL + '\n')

    def calc(self):
        if not self.values:
            printout = []
            for n, f in SAFE:
                if f != None:
                    printout.append(n)

            self.chat("Available functions: " + ", ".join(printout))
            return
        try:
            result = eval(' '.join(self.values), {"__builtins__": None}, self.safe_calc)
        except:
            result = NICK + " not smart enough to do that."

        self.chat(result)

    def all(self):
        peeps = self.members
        try:
            peeps.remove(self.lastsender)
        except:
            self.chat('List incoherrent')
            return

        peeps = ', '.join(peeps)
        self.chat(peeps + ', ' + self.lastsender + ' has something very important to say.')

    def bored(self):
        if not self.members:
            return

        self.announce("Chirp chirp. Chirp Chirp.")

        # The behavior below is known to be highly obnoxious
        # self.act("is bored.")
        # self.act(random.choice(BOREDOM) + " " + random.choice(self.members))

    def define(self):
        if len(self.values) != 2:
            self.chat("Please submit a word and its possible parts of speech")
            return

        word = self.values[0]
        parts = list(self.values[1])

    def learnword(self):

        banned = []

        if self.lastsender in banned:
            self.chat("My daddy says not to listen to you.")
            return

        if not self.values:
            self.chat(NICK + " ponders the emptiness of meaning.")
            return

        if not re.match("^[A-Za-z]+$", self.values[0].strip()):
            self.chat(NICK + " doesn't think that's a word.")
            return

        open(STORAGE + "/natword", 'a').write(self.values[0].strip() + '\n')
        self.chat(NICK + " learn new word!", self.lastsender)

    def acronymit(self, base):

        acronym = list(base.upper())
        output = []

        wordbank = []
        for line in open(STORAGE + "/" + ACROLIB):
            wordbank.append(line.strip())

        for letter in acronym:
            good = False
            while not good:
                word = random.choice(wordbank).capitalize()
                if word[:1] == letter:
                    output.append(word)
                    good = True

        return " ".join(output)

    def think(self):
        if not self.values:
            self.chat("About what?")
            return

        if not re.match("^[A-Za-z]+$", self.values[0]) and self.lastsender == "erikbeta":
            self.chat("Fuck off erik.")
            return

        if not re.match("^[A-Za-z]+$", self.values[0]):
            self.chat(NICK + " no want to think about that.")
            return

        output = self.acronymit(self.values[0])
        self.chat(output)

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

        if content[:1] == "~":
            self.command(nick, content)
            return

        match_urls = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = match_urls.findall(content)
        if len(urls):
            self.linker(urls)
            return

        self.broca.parse(content)

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
            response = self.pageopen('https://api.twitter.com/1/statuses/show.json?id=%s' % url[1])
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

            urlbase = self.pageopen(url)
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
            username = "okdrink"
            password = "PGkbLJCAVfF8jhAtZD8Y"
            base64string = base64.encodestring('%s:%s' % (username, password))[:-1]

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

    def update(self):

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
        if not self.stockquote(self.lastcommand,True):
            self.chat(NICK + " cannot do this thing :'(")

    def showsettings(self):
        for name, value in SAFESET:
            sleep(1)
            self.chat(name + " : " + str(value))

    def pageopen(self,url):
        try:
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urlbase = opener.open(url).read()
            urlbase = re.sub('\s+', ' ', urlbase).strip()
        except:
            return False

        return urlbase
        
