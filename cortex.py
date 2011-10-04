import socket 
import string 
import simplejson as json
import os
import re
import random
import threading
import urllib2
import urllib
from time import *

import acro,settings
from acro import Acro
from math import * 
from settings import *

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
            "help":self.showlist,    
            "distaste":self.distaste,    
            "reboot":self.master.die,
            "reload":self.master.reload,    
            "update":self.update,    
            "roque":self.acroengine,    
            "acro":self.acroengine,    
            "love":self.love,    
            "hate":self.hate,    
            "boards":self.boards,    
            "think":self.think,    
            "settings":self.showsettings,    
            "learnword":self.learnword,    
            "cry":self.cry,    
            "calc":self.calc,    
            "bored":self.bored,    
            "register":self.getnames,    
            "rules":self.rules,    
            "mom":self.mom,    
            "whatvinaylost":self.whine,    
            "say":self._say,    
            "act":self._act,    
            "somethingabout":self.somethingabout,    
            "mem":self.somethingabout,    
            "next":self.next,    
            "prev":self.prev,    
            "oldest":self.oldest,    
            "latest":self.latest,    
        }.get(what,self.default)()

    def showlist(self):
        list = [
            "~help <show this message>",
            "~love <command " + NICK + " to love>",
            "~distaste <command " + NICK + " to express disastisfaction>",
            "~distaste url <expand " + NICK + "'s to disastisfaction repertoire>",
            "~settings <show current settings>",
            "~update SETTING_NAME value <change a setting>",
            "~rules <print the rules for the acro game>",
            "~roque [pause|resume|end] <start acro game>",
            "~think ABC <come up with an acronym for submitted letters>",
            "~learnword someword <add a word to bot's acronym library>",
            "~boards <show cumulative acro game scores>",
            "~calc <show available python math functions>",
            "~calc equation <run a simple calculation>",
            "~mem <search logs for phrase and print the most recent>",
            "~next <after mem, get the next phrase memory>",
            "~prev <after mem, get the previous phrase memory>",
            "~latest <after mem, get the latest phrase memory>",
            "~oldest <you see where this is going>",
            "~mom <randomly reprint a message containing 'mom'>",
            "~reload <reload libraries>",
            "~reboot <guess>",
        ]

        for command in list:
            sleep(1)
            self.say(command,self.lastsender)

    def somethingabout(self):
        if not self.values:
            self.say("Something about what?")
            return

        self.say("Recalling...")
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
        self.say(self.memories[self.mempoint])

    def nomem(self):
        if not self.memories:
            self.say("Nothing in memory.")
            return True
        else:
            return False

    def next(self):
        if self.nomem():
            return
        if self.mempoint == len(self.memories) - 1:
            self.say("That's the most recent thing I can remember.")
            return
        self.mempoint += 1
        self.remember()

    def prev(self):
        if self.nomem():
            return
        if self.mempoint == 0: 
            self.say("That's as far back as I can remember.")
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
        self.say("Yep. Vinay used to have 655 points at 16 points per round. Now they're all gone, due to technical issues. Poor, poor baby.")
        self.act("weeps for Vinay's points.")
        self.say("The humanity!")

    def validate(self):
        if not self.values:
            return False
        if self.lastsender != "chiyou":
            return False

        return True

    def _say(self):
        if self.validate():
            self.say(" ".join(self.values))

    def _act(self):
        if self.validate():
            self.act(" ".join(self.values))

    def mom(self):
        momlines = []
        for line in open(BRAIN + "/mom.log"):
            momlines.append(line)

        self.say("Hey " + random.choice(self.members) + "! " + random.choice(momlines))

    def rules(self):
        self.say("1 of 6 start game with ~roque.")
        self.say("2 of 6 when the acronym comes up, type /msg " + NICK + " your version of what the acronym stands for.")
        self.say("3 of 6 each word of your submission is automatically updated unless you preface it with '-', so 'do -it up' will show as 'Do it Up'.")
        self.say("4 of 6 when the voting comes up, msg " + NICK + " with the number of your vote.")
        self.say("5 of 6 play till the rounds are up.")
        self.say("6 of 6 " + NICK + " plays by default. Run ~update BOTPLAY False to turn it off.")

    def getnames(self):
        self.gettingnames = True
        self.sock.send('NAMES '+ CHANNEL + '\n')

    def calc(self):
        if not self.values:
            printout = []
            for n,f in SAFE:
                if f != None:
                    printout.append(n)

            self.say("Available functions: " + ", ".join(printout))
            return
        try:
            result = eval(' '.join(self.values),{"__builtins__":None},self.safe_calc)
        except:
            result = NICK + " not smart enough to do that."

        self.say(result,self.lastsender)

    def bored(self):
        if not self.members:
            return

        self.say("Chirp chirp. Chirp Chirp.")

        # The behavior below is known to be highly obnoxious
        # self.act("is bored.")
        # self.act(random.choice(BOREDOM) + " " + random.choice(self.members))

    def cry(self):
        self.act("cries.")

    def define(self):
        if len(self.values) != 2:
            self.say("Please submit a word and its possible parts of speech")
            return

        word = self.values[0]
        parts = list(self.values[1])

    def learnword(self):
    
        banned = []

        if self.lastsender in banned:
            self.say("My daddy says not to listen to you.",self.lastsender)
            return

        if not self.values:
            self.say(NICK + " ponders the emptiness of meaning.",self.lastsender)
            return
        
        if not re.match("^[A-Za-z]+$",self.values[0].strip()):
            self.say(NICK + " doesn't think that's a word.",self.lastsender)
            return
            
        open(BRAIN + "/natword",'a').write(self.values[0].strip() + '\n')
        self.say(NICK + " learn new word!",self.lastsender)

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

    def think(self):
        if not self.values:
            self.say("About what?",self.lastsender)
            return

        if not re.match("^[A-Za-z]+$",self.values[0]) and self.lastsender == "erikbeta":
            self.say("Fuck off erik.",self.lastsender)
            return

        if not re.match("^[A-Za-z]+$",self.values[0]):
            self.say(NICK + " no want to think about that.",self.lastsender)
            return

        output = self.acronymit(self.values[0])
        self.say(output,self.lastsender)


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

            self.say(player + ": " + str(score) + " (" + str(average) + " per round)")

    def acroengine(self):
  
        if self.acro:
            if self.values:
                action = self.values[0]
                if action == "pause":
                    if self.acro.wait:
                        self.acro.paused = True
                        self.say("Game paused")
                    else:
                        self.say("You can only pause between rounds.")
                        
                elif action == "resume":
                    self.acro.paused = False
                    self.say("Game on")
                elif action == "end": 
                    self.acro.killgame = True
                else:
                    self.say("Not a valid action")

                return
            
            self.say("Already a game in progress")
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
    
        if content.find(NICK + " sucks") != -1:
            self.say(nick + "'s MOM sucks")

        if content[:1] == "~":
            self.command(nick,content)

        if "mom" in content.translate(string.maketrans("",""), string.punctuation).split():
            open(BRAIN + "/mom.log",'a').write(content + '\n')

        if content.lower().find("oh snap") != -1:
            if nick.lower().find("cross") != -1:
                self.say("[crickets]")
            else:
                self.say("yeah WHAT?? Oh yes he DID")
     
    def update(self):

        if not self.values or len(self.values) != 2:
            self.say("Must name SETTING and value, please")
            return

        pull = ' '.join(self.values)

        if pull.find("'") != -1 or pull.find("\\") != -1 or pull.find("`") != -1:
            self.say("No single quotes, backtics, or backslashes, thank you.")
            return

        setting,value = pull.split(' ',1)

        safe = False
        for safesetting,val in SAFESET:
            if setting == safesetting:
                safe = True
                break;

        if not safe:
            self.say("That's not a safe value to change.")
            return

        rewrite = "sed 's/" + setting + " =.*/" + setting + " = " + value + "/'"
        targeting = ' <settings.py >tmp'
        reset = 'mv tmp settings.py'

        os.system(rewrite + targeting)
        os.system(reset)

        self.say(NICK + " rewrite brain. Feel smarter.")

    def love(self):
        if self.values and self.values[0] == "self":
            self.act("masturbates vigorously.")
        else:
            self.say(NICK + " cannot love. " + NICK + " is only machine :'(")

    def hate(self):
        self.say(NICK + " knows hate. " + NICK + " hates many things.")

    def distaste(self):

        if self.values:
            
            url = urllib.quote_plus(self.values[0])
            roasted = urllib2.urlopen(SHORTENER + url).read()

            open(DISTASTE,'a').write(roasted + '\n')
            self.say("Another one rides the bus")
            return

        lines = []
        for line in open(DISTASTE):
            lines.append(line)
         
        self.say(random.choice(lines))

    def say(self,message,whom = False):
        if not whom or self.context == CHANNEL:
            whom = CHANNEL
        self.sock.send('PRIVMSG '+ whom +' :' + str(message) + '\n')

    def act(self,message,whom = False):
        message = "\001ACTION " + message + "\001"
        self.say(message,whom)

    def default(self):
        self.say(NICK + " cannot do this thing :'(")

    def showsettings(self):
        for name,value in SAFESET:
            sleep(1)
            self.say(name + " : " + str(value),self.lastsender)


