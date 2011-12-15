import socket 
import string 
import simplejson as json
import os
import re
import random
import threading
import urllib2
import urllib
import ystock 
from BeautifulSoup import BeautifulSoup as soup

from math import * 
from time import *

import settings
import acro
import holdem 
import redmine
import broca

from settings import *
from acro import Acro
from holdem import Holdem 
from redmine import Redmine
from broca import Broca 

class Cortex:

    def __init__(self,master):
        self.acro = False
        self.values = False
        self.master = master
        self.context = CHANNEL
        self.sock = master.sock
        self.gettingnames = True 
        self.members = [] 
        self.memories = False
        self.boredom = int(mktime(localtime())) 
        self.namecheck = int(mktime(localtime())) 
        self.safe_calc = dict([ (k, locals().get(k, f)) for k,f in SAFE])
        self.redmine = Redmine(self)
        self.holdem = Holdem(self)
        self.broca = Broca(self)

    def reload(self):
        reload(acro)
        reload(redmine)
        reload(broca)
        reload(holdem)
        from acro import Acro
        from holdem import Holdem 
        from redmine import Redmine
        from broca import Broca 
        self.redmine = Redmine(self)
        self.holdem = Holdem(self)
        self.broca = Broca(self)

    def monitor(self,sock):
        line = self.sock.recv(500)
        line = line.strip()
        
        currenttime = int(mktime(localtime())) 
        if line != '':
            self.logit(line + '\n')
        
        if self.gettingnames:
            if line.find("* " + CHANNEL) != -1:
                all = line.split(":")[2]
                self.gettingnames = False
                self.members = all.split()

        if line.find('PING') != -1:
            self.sock.send('PONG ' + line.split()[1] + '\n')
        elif line.find('PRIVMSG') != -1:
            self.boredom = int(mktime(localtime())) 
            content = line.split(' ',3)
            self.context = content[2]

            if self.acro:
                if self.context == NICK:
                    self.acro.input(content)

            self.parse(line)
        
        if currenttime - self.namecheck > 60:
            self.namecheck = int(mktime(localtime())) 
            self.getnames()

        if currenttime - self.boredom > PATIENCE:
            self.boredom = int(mktime(localtime())) 
            if random.randint(1,10) == 7:
                self.bored()
    
    def command(self,sender,cmd):
        components = cmd.split()
        what = components.pop(0)[1:]
    
        if components:
            self.values = components
        else:
            self.values = False

        self.logit(sender + " sent command: " + what + "\n")
        self.lastsender = sender    

        {
            # General
            "help":self.showlist,    
            "love":self.love,    
            "hate":self.hate,    
            "think":self.think,    
            "settings":self.showsettings,    
            "learnword":self.learnword,    
            "cry":self.cry,    
            "calc":self.calc,    
            "bored":self.bored,    
            "register":self.getnames,    
            "say":self._say,    
            "act":self._act,    
            "q":self.stockquote,    
            "munroesecurity":self.password,    

            # Memory
            "somethingabout":self.somethingabout,    
            "mem":self.somethingabout,    
            "next":self.next,    
            "prev":self.prev,    
            "oldest":self.oldest,    
            "latest":self.latest,    

            # System
            "update":self.update,    
            "reboot":self.master.die,
            "reload":self.master.reload,    

            # Redmine
            "hot":self.redmine.showhotfix,
            "tickets":self.redmine.showtickets,
            "register":self.redmine.register,
            "assign":self.redmine.assignment,
            "snag":self.redmine.assignment,
            "detail":self.redmine.showdetail,

            # Language
            "whatmean":self.broca.whatmean,
            "def":self.broca.whatmean,

            # Acro
            "roque":self.acroengine,    
            "acro":self.acroengine,    
            "boards":self.boards,    
            "rules":self.rules,    

            # Holdem
            "holdem":self.holdemengine,    
            "bet":self.holdem.bet,    
            "call":self.holdem.callit,    
            "raise":self.holdem.raiseit,    
            "pass":self.holdem.knock,    
            "fold":self.holdem.fold,    
            "allin":self.holdem.allin,    

            # Nerf out for work bots
            "distaste":self.distaste,    
            "mom":self.mom,    
            "whatvinaylost":self.whine,    
        }.get(what,self.default)()

    def showlist(self):
        list = [
            "~help <show this message>",
            "~register [api key] <register your redmine api key with MongoBot>",
            "~hot <display all unassigned hotfixes>",
            "~q <get stock quote>",
            "~detail [ticket number] <get a ticket description>",
            "~snag [ticket number] <assign a ticket to yourself>",
            "~assign [user nick] [ticket number] <assign a ticket to someone else>",
            "~tickets [user; optional] <show assigned tickets for user>",
            "~love <command " + NICK + " to love>",
            "~settings <show current settings>",
            "~update SETTING_NAME value <change a setting>",
            "~think ABC <come up with an acronym for submitted letters>",
            "~learnword someword <add a word to bot's acronym library>",
            "~whatmean someword <look up word in local database or wordnik>",
            "~calc <show available python math functions>",
            "~calc equation <run a simple calculation>",
            "~somethingabout <search logs for phrase and print the most recent>",
            "~next <after mem, get the next phrase memory>",
            "~prev <after mem, get the previous phrase memory>",
            "~latest <after mem, get the latest phrase memory>",
            "~oldest <you see where this is going>",
            "~reload <reload libraries>",
            "~reboot <guess>",

            # Nerf out for work bots
            "~rules <print the rules for the acro game>",
            "~roque [pause|resume|end] <start acro game>",
            "~boards <show cumulative acro game scores>",
            "~mom <randomly reprint a message containing 'mom'>",
            "~distaste <command " + NICK + " to express disastisfaction>",
            "~distaste url <expand " + NICK + "'s to disastisfaction repertoire>",
        ]

        for command in list:
            sleep(1)
            self.chat(command)

    def stockquote(self):
        if not self.values:
            self.chat("What stock?")
            return

        stock = self.values[0]
        try:
            info = ystock.get_all(stock.upper())
        except:
            self.chat("Couldn't find anything")

        message = [stock.upper() + ": " + info["name"][1:]]
        message.append("Current: " + str(info["price"])) 
        message.append("Change: " + str(info["change"])) 
        message.append("Volume: " + str(info["volume"])) 
        message.append("Market Cap: " + str(info["market_cap"])) 
        message.append("Dividend per Share: " + str(info["dividend_per_share"])) 
        
        self.chat(', '.join(message))


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
                    whom,message = line[1:].split(":",1)
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
        if self.lastsender != "chiyou":
            return False

        return True

    def _say(self):
        if self.validate():
            self.announce(" ".join(self.values))

    def _act(self):
        if self.validate():
            self.act(" ".join(self.values),True)

    def mom(self):
        momlines = []
        for line in open(BRAIN + "/mom.log"):
            momlines.append(line)

        self.announce(random.choice(momlines))

    def rules(self):
        self.chat("1 of 6 start game with ~roque.")
        self.chat("2 of 6 when the acronym comes up, type /msg " + NICK + " your version of what the acronym stands for.")
        self.chat("3 of 6 each word of your submission is automatically updated unless you preface it with '-', so 'do -it up' will show as 'Do it Up'.")
        self.chat("4 of 6 when the voting comes up, msg " + NICK + " with the number of your vote.")
        self.chat("5 of 6 play till the rounds are up.")
        self.chat("6 of 6 " + NICK + " plays by default. Run ~update BOTPLAY False to turn it off.")

    def getnames(self):
        self.gettingnames = True
        self.sock.send('NAMES '+ CHANNEL + '\n')

    def calc(self):
        if not self.values:
            printout = []
            for n,f in SAFE:
                if f != None:
                    printout.append(n)

            self.chat("Available functions: " + ", ".join(printout))
            return
        try:
            result = eval(' '.join(self.values),{"__builtins__":None},self.safe_calc)
        except:
            result = NICK + " not smart enough to do that."

        self.chat(result)

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
        
        if not re.match("^[A-Za-z]+$",self.values[0].strip()):
            self.chat(NICK + " doesn't think that's a word.")
            return
            
        open(BRAIN + "/natword",'a').write(self.values[0].strip() + '\n')
        self.chat(NICK + " learn new word!",self.lastsender)

    def acronymit(self,base):
 
        acronym = list(base.upper())
        output = []
        
        wordbank = []
        for line in open(BRAIN + "/" + ACROLIB):
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
        for line in open(BRAIN + "/" + ACROLIB):
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

        if not re.match("^[A-Za-z]+$",self.values[0]) and self.lastsender == "erikbeta":
            self.chat("Fuck off erik.")
            return

        if not re.match("^[A-Za-z]+$",self.values[0]):
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
                            player,score,toss = line.split()
                            if player in scores:
                                scores[player]['score'] += int(score)
                                scores[player]['rounds'] += 1
                            else:
                                scores[player] = {'score':int(score),'rounds':1}
                        except:
                            continue
        
        for player in scores:
            score = scores[player]['score']
            average = score/scores[player]['rounds']

            self.chat(player + ": " + str(score) + " (" + str(average) + " per round)")

    def holdemengine(self):
        #if self.holdem:
        #    self.chat("Already a game in progress")
        #    return
        
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

    def logit(self,what):
        open(LOG,'a').write(what)

    def parse(self,msg):
        info,content = msg[1:].split(':',1)
        try:
            sender,type,room = info.strip().split()
        except:
            return

        try:
            nick = sender.split('!')[0]
            ip = sender.split('@')[1]
        except:
            return

        self.lastsender = nick
    
        if content.find(NICK + " sucks") != -1:
            self.chat(nick + "'s MOM sucks")

        if content[:1] == "~":
            self.command(nick,content)

        if "mom" in content.translate(string.maketrans("",""), string.punctuation).split():
            open(BRAIN + "/mom.log",'a').write(content + '\n')

        if content.lower().find("oh snap") != -1:
            if nick.lower().find("cross") != -1:
                self.announce("[crickets]")
            else:
                self.announce("yeah WHAT?? Oh yes he DID")

        match_urls = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

        urls =  match_urls.findall(content)
        if len(urls):
            self.linker(urls)
             

    def linker(self,urls):

        for url in urls:
            # TODO make this better
            try:
                opener = urllib2.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urlbase = opener.open(url).read()
                urlbase = urlbase.replace("\t"," ").replace("\n"," ").strip()
                cont = soup(urlbase)
                roasted = urllib2.urlopen(SHORTENER + url).read()
                title = cont.title.string
                self.chat(title + " @ " + roasted)
            except:
                self.chat("Somthin' went 'n' done fucked up")

     
    def update(self):

        if not self.values or len(self.values) != 2:
            self.chat("Must name SETTING and value, please")
            return

        pull = ' '.join(self.values)

        if pull.find("'") != -1 or pull.find("\\") != -1 or pull.find("`") != -1:
            self.chat("No single quotes, backtics, or backslashes, thank you.")
            return

        setting,value = pull.split(' ',1)

        safe = False
        for safesetting,val in SAFESET:
            if setting == safesetting:
                safe = True
                break;

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

            open(DISTASTE,'a').write(roasted + '\n')
            self.chat("Another one rides the bus")
            return

        lines = []
        for line in open(DISTASTE):
            lines.append(line)
         
        self.chat(random.choice(lines))

    def announce(self,message,whom = False):
        try:
            self.sock.send('PRIVMSG '+ CHANNEL +' :' + str(message) + '\n')
        except:
            self.sock.send('PRIVMSG '+ CHANNEL +' :Having trouble saying that for some reason\n')


    def chat(self,message,target = False):
        if target:
            whom = target
        elif self.context == CHANNEL:
            whom = CHANNEL
        else:
            whom = self.lastsender

        try:
            self.sock.send('PRIVMSG '+ whom +' :' + str(message) + '\n')
        except:
            self.sock.send('PRIVMSG '+ whom +' :Having trouble saying that for some reason\n')
       
    def act(self,message,public = False):
        message = "\001ACTION " + message + "\001"
        if public:
            self.announce(message)
        else:
            self.chat(message)

    def default(self):
        self.chat(NICK + " cannot do this thing :'(")

    def showsettings(self):
        for name,value in SAFESET:
            sleep(1)
            self.chat(name + " : " + str(value))


