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

from BeautifulSoup import BeautifulSoup as soup

import acro
import holdem
import redmine
import broca
import stocks

from settings import *
from secrets import *
from acro import Acro
from holdem import Holdem
from redmine import Redmine
from broca import Broca
from stocks import Stock

# TODO: standardize url grabber


def unescape(text):  # utility, should probably have a utils file
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub("&#?\w+;", fixup, text)


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

        # chess stuff
        self.chessgrid = []
        self.resetchess()

        # connect the bot
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

        # Ignore ~[0-9]+ commands
        is_invalid = re.search("^[0-9]+", what)
        if is_invalid:
            return

        if components:
            self.values = components
        else:
            self.values = False

        self.logit(sender + " sent command: " + what + "\n")
        self.lastsender = sender
        self.lastcommand = what

        {
            # General
            "help": self.showlist,
            "love": self.love,
            "hate": self.hate,
            "settings": self.showsettings,
            "reward": self.reward,
            "think": self.think,
            "learnword": self.learnword,
            "cry": self.cry,
            "calc": self.calc,
            "bored": self.bored,
            "names": self.getnames,
            "say": self._say,
            "act": self._act,
            "g": self.goog,
            "ety": self.ety,
            "buzz": self.buzz,
            "fml": self.fml,
            "anagram": self.anagram,
            "munroesecurity": self.password,
            "skynet": self.skynet,
            "table": self.table,
            "intros": self.intros,
            "source": self.source,
            "aleksey": self.shitalekseysays,
            "workat": self.workat,
            "companies": self.companies,
            "company": self.company,
            "all": self.all,
            "weather": self.weather,

            # Finance
            "q": self.stockquote,
            "portfolio": self.portfolio,
            "btc": self.btc,

            # Memory
            "somethingabout": self.somethingabout,
            "mem": self.somethingabout,
            "next": self.next,
            "prev": self.prev,
            "oldest": self.oldest,
            "latest": self.latest,

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

            # Acro
            "roque": self.acroengine,
            "acro": self.acroengine,
            "boards": self.boards,
            "rules": self.rules,

            # Chess
            "chess": self.chess,
            "move": self.move,
            "resetchess": self.resetchess,

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

            # Nerf out for work bots
            "distaste": self.distaste,
            "mom": self.mom,
            "whatvinaylost": self.whine,
        }.get(what, self.default)()

    def showlist(self):
        list = { 
            "g":[
                "~g [what]<search google>",
                "~love <command " + NICK + " to love>",
                "~hate <command " + NICK + " to hate>",
                "~settings <show current settings>",
                "~reload <reload libraries>",
                "~reboot <guess>",
                "~reward <give someone a reward>",
                "~cry <make " + NICK + " cry>",
                "~bored <make " + NICK + " bored>",
                "~update SETTING_NAME [value] <change a setting>",
                "~mom <randomly reprint a message containing 'mom'>",
                "~distaste <command " + NICK + " to express disastisfaction>",
                "~distaste [url] <expand " + NICK + "'s to disastisfaction repertoire>",
                "~fml <grab random fml entry>",
                "~munroesecurity <generate passward according to http://xkcd.com/936/>",
                "~skynet <launch skynet>",
                "~table <throw table>",
                "~intros <show history of " + CHANNEL + ">",
                "~source <link to repo for " + NICK + ">",
                "~aleksey <pull a quote from shitalekseysays.com>",
                "~workat <register what company you work at>",
                "~companies <show who works where>",
                "~company <show the company a specific person works for>",
                "~weather <get weather by zip code>",
            ],
            "f":[
                "~q [stock symbol]<get stock quote>",
                "~portfolio [stock symbol]<add stock to your portfolio>",
                "~portfolio <show your portfolio>",
                "~portfolio clear <empty your portfolio>",
                "~btc <get current Bitcoin trading information>",
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
            "m":[
                "~somethingabout/~mem <search logs for phrase and print the most recent>",
                "~next <after mem, get the next phrase memory>",
                "~prev <after mem, get the previous phrase memory>",
                "~latest <after mem, get the latest phrase memory>",
                "~oldest <you see where this is going>",
            ],
            "c":[
                "~chess <show chessboard>",
                "~move [a-f][1-8] [a-f][1-8] <move piece [from] [to]>",
                "~resetchess <reset chessboard>",
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

        if not self.values or self.values[0] not in list: 
            categories = [
                "(g)eneral", 
                "(l)anguage and math", 
                "(m)emory", 
                "(a)cro", 
                "(h)oldem", 
                "(c)hess", 
                "(r)edmine",
                "(f)inance",
            ]
            self.chat("Use ~help [what] where what is " + ", ".join(categories))
            return

        which = self.values[0]

        for command in list[which]:
            sleep(1)
            self.chat(command)

    def weather(self):
        if not self.values or not re.search("^\d{5}", self.values[0]): 
            self.chat("Please enter a zip code.")
            return
        
        zip = self.values[0]
        url = "http://api.wunderground.com/api/%s/conditions/q/%s.json" % (WEATHER, zip)
 
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

    def table(self):
        self.chat(u'\u0028' + u'\u256F' + u'\u00B0' + u'\u25A1' + u'\u00B0' + u'\uFF09' + u'\u256F' + u'\uFE35' + u'\u0020' + u'\u253B' + u'\u2501' + u'\u253B')

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

    def resetchess(self):

        self.pieces = dict(
            br=u'\u265c',
            bn=u'\u265e',
            bb=u'\u265d',
            bq=u'\u265b',
            bk=u'\u265a',
            bp=u'\u265f',
            wr=u'\u2656',
            wn=u'\u2658',
            wb=u'\u2657',
            wq=u'\u2655',
            wk=u'\u2654',
            wp=u'\u2659',
        )
        self.chessgrid = [
            ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
            ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
            ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr'],
        ]

    def chess(self):
        squares = [u'\u25fc', u'\u25fb']
        flip = 0
        count = 8
        for row in self.chessgrid:
            rowset = [str(count)]
            for space in row:
                if space:
                    rowset.append(self.pieces[space])
                else:
                    rowset.append(squares[flip])
                flip = (flip + 1) % 2

            flip = (flip + 1) % 2
            count -= 1

            self.chat(' '.join(rowset))

        self.chat(u'  a\u00a0b\u00a0c\u00a0d\u00a0e\u00a0f\u00a0g\u00a0h')

    def move(self):
        if not self.values:
            self.chat("Bad format")
            return

        if len(self.values) < 2:
            self.chat("Not enough values")
            return

        start = self.values[0]
        finis = self.values[1]
        trans = dict(a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7)

        if start in self.pieces:
            piece = self.pieces[start]
        else:
            x = 8 - int(start[1:])
            y = trans[start[:1]]

            piece = self.chessgrid[x][y]
            if not piece:
                self.chat("No piece there")
                return
            self.chessgrid[x][y] = ''
            
        x = 8 - int(finis[1:])
        y = trans[finis[:1]]

        self.chessgrid[x][y] = piece
        self.chess()

    def skynet(self):
        self.chat("Activating.")

    def reward(self):
        if not self.values:
            self.chat("Reward whom?")
            return
        
        kinder = self.values[0]
        self.chat("Good job, " + kinder + ". Here's your star: " + self.colorize(u'\u2605',"yellow"))
        self.act(" pats " + kinder + "'s head.")

    def portfolio(self):

        whom = self.lastsender

        if self.values and self.values[0] == 'clear':
            drinker = Drinker.objects(name = whom)[0]
            if drinker and drinker.portfolio:
                drinker.portfolio = []
                drinker.save()

            return

        if self.values:
            for symbol in self.values:
                stock = Stock(symbol)
                if not stock or len(symbol) > 8:
                    self.chat("Could not add '" + symbol + "'")
                    continue
                
                stock.save(whom)
            return

        drinker = Drinker.objects(name = whom)[0]
        if drinker and drinker.portfolio:
            for symbol in drinker.portfolio:
                stock = Stock(symbol)
                showit = stock.showquote(self.context)
                self.chat(showit)
        else:
            self.chat("No stocks saved")

    def stockquote(self, symbol = False, default = False):
        if not symbol:
            symbol = self.values
        
        if not symbol:
            self.chat("Enter a symbol")
            return

        if not default:
            symbol = symbol[0] 

        stock = Stock(symbol)
        showit = stock.showquote(self.context)

        if not showit and default:
            return False
        
        if not showit:
            self.chat("Couldn't find company.")
            return

        self.chat(showit)
        return True
        
    def fml(self):
        db = MySQLdb.connect("localhost","peter",SQL_PASSWORD,"peter_stilldrinking") 
        cursor = db.cursor()
        cursor.execute("SELECT * FROM fmls ORDER BY RAND() LIMIT 0,1;")
        entry = cursor.fetchone()
        # id
        # fid
        # entry
        # agree
        # ydi
        # calc
        # gender
        # date
        # time
        # location
        # intimate
        fml = entry[2]
        self.chat(fml)

    def shitalekseysays(self):
        url = 'https://spreadsheets.google.com/feeds/list/0Auy4L1ZnQpdYdERZOGV1bHZrMEFYQkhKVHc4eEE3U0E/od6/public/basic?alt=json'

        try:
            response = urllib2.urlopen(url).read()
            json = simplejson.loads(response)
        except:
            self.chat('Somethin dun goobied.')
            return

        entry = choice(json['feed']['entry'])
        self.chat(entry['title']['$t'])

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

    def somethingabout(self):
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

    def next(self):
        if self.nomem():
            return
        if self.mempoint == len(self.memories) - 1:
            self.chat("That's the most recent thing I can remember.")
            return
        self.mempoint += 1
        self.remember()

    def prev(self):
        if self.nomem():
            return
        if self.mempoint == 0:
            self.chat("That's as far back as I can remember.")
            return
        self.mempoint -= 1
        self.remember()

    def oldest(self):
        if self.nomem():
            return
        self.mempoint = 0
        self.remember()

    def latest(self):
        if self.nomem():
            return
        self.mempoint = len(self.memories) - 1
        self.remember()

    def whine(self):
        self.chat("Yep. Vinay used to have 655 points at 16 points per round. Now they're all gone, due to technical issues. Poor, poor baby.")
        self.act("weeps for Vinay's points.")
        self.chat("The humanity!")

    def validate(self):
        if not self.values:
            return False
        if self.lastsender != OWNER:
            return False

        return True

    def _say(self):
        if self.validate():
            self.announce(" ".join(self.values))

    def _act(self):
        if self.validate():
            self.act(" ".join(self.values), True)

    def mom(self):
        momlines = []
        for line in open(LOGDIR + "/mom.log"):
            momlines.append(line)

        self.chat(random.choice(momlines))

    def buzz(self):
        bsv = []
        bsa = []
        bsn = []
        for verb in open(STORAGE + "/buzz/bs-v"):
            bsv.append(str(verb).strip())

        for adj in open(STORAGE + "/buzz/bs-a"):
            bsa.append(str(adj).strip())

        for noun in open(STORAGE + "/buzz/bs-n"):
            bsn.append(str(noun).strip())

        buzzed = [
            random.choice(bsv),
            random.choice(bsa),
            random.choice(bsn),
        ]

        self.chat(' '.join(buzzed))

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

    def cry(self):
        self.act("cries.")

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

    def password(self):

        output = []
        wordbank = []
        for line in open(STORAGE + "/" + ACROLIB):
            wordbank.append(line.strip())

        count = 0
        while count < 4:
            word = random.choice(wordbank).lower()
            output.append(word)
            count += 1

        self.chat(" ".join(output))

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

    def love(self):
        # Nerf out for work bots
        if self.values and self.values[0] == "self":
            self.act("masturbates vigorously.")
        else:
            self.chat(NICK + " cannot love. " + NICK + " is only machine :'(")

    def hate(self):
        self.chat(NICK + " knows hate. " + NICK + " hates many things.")

    def distaste(self):

        if self.values:
            url = urllib.quote_plus(self.values[0])
            roasted = urllib2.urlopen(SHORTENER + url).read()

            open(DISTASTE, 'a').write(roasted + '\n')
            self.chat("Another one rides the bus")
            return

        lines = []
        for line in open(DISTASTE):
            lines.append(line)

        self.chat(random.choice(lines))

    # instead of presuming to predict what
    # will be colored, make it easy to prep 
    # string elements
    def colorize(self, text, color):
        
        colors = {
            "white":0, 
            "black":1, 
            "blue":2,       #(navy)
            "green":3, 
            "red":4, 
            "brown":5,      #(maroon)
            "purple":6, 
            "orange":7,     #(olive)
            "yellow":8, 
            "lightgreen":9, #(lime)
            "teal":10,      #(a green/blue cyan)
            "lightcyan":11, #(cyan) (aqua)
            "lightblue":12, #(royal)
            "pink":13,      #(light purple) (fuchsia)
            "grey":14, 
            "lightgrey":15, #(silver)
        }

        if isinstance(color,str):
            color = colors[color]

        return "\x03" + str(color) + text + "\x03"


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
        
