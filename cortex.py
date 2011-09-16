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
from settings import *

class Cortex:

    def __init__(self,master):
        self.acro = False
        self.values = False
        self.master = master
        self.context = CHANNELINIT
        self.sock = master.sock

    def monitor(self,sock):
        line = self.sock.recv(500)
        line = line.strip()
        if line != '':
            self.logit(line + '\n')
        
        if line.find('PING') != -1:
            self.sock.send('PONG ' + line.split()[1] + '\n')
        elif line.find('PRIVMSG') != -1:
            content = line.split(' ',3)
            self.context = content[2]

            if self.acro:
                if self.context == NICK:
                    self.acro.input(content)

            self.parse(line)
    
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
            "love":self.love,    
            "hate":self.hate,    
            "boards":self.boards,    
            "think":self.think,    
            "settings":self.showsettings,    
            "learnword":self.learnword,    
        }.get(what,self.default)()

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
            
        open(BRAIN + "/wordbank",'a').write(self.values[0].strip() + '\n')
        self.say(NICK + " learn new word!",self.lastsender)

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

        acronym = list(self.values[0].upper())
        output = []
        
        wordbank = []
        for line in open(BRAIN + "/wordbank"):
            wordbank.append(line.strip())

        for letter in acronym:
            good = False
            while not good:
                word = random.choice(wordbank).capitalize()
                if word[:1] == letter:
                    output.append(word)
                    good = True 
        
        self.say(" ".join(output),self.lastsender)


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

        if content.find("mom") != -1:
            open(BRAIN + "/mom.log",'a').write(content + '\n')
     
    def update(self):

        if not self.values or len(self.values) != 2:
            self.say("Must name SETTING and value, please")
            return

        pull = ' '.join(self.values)

        if pull.find("'") != -1 or pull.find("\\") != -1 or pull.find("`") != -1:
            self.say("No single quotes, backtics, or backslashes, thank you.")
            return

        setting,value = pull.split(' ',1)

        rewrite = "sed 's/" + setting + ".*/" + setting + " = " + value + "/'"
        targeting = ' <settings.py >tmp'
        reset = 'mv tmp settings.py'

        os.system(rewrite + targeting)
        os.system(reset)

        self.say(NICK + " rewrite brain. Feel smarter.")

    def love(self):
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
        if not whom or self.context == CHANNELINIT:
            whom = CHANNELINIT
        self.sock.send('PRIVMSG '+ whom +' :' + message + '\n')

    def default(self):
        self.say(NICK + " cannot do this thing :'(")

    def showsettings(self):
        for line in open("settings.py"):
            if line.strip() == "# STOP":
                return
            self.say(line.strip())

    def showlist(self):
        list = [
            "~help <show this message>",
            "~love <command " + NICK + " to love>",
            "~distaste <command " + NICK + " to express disastisfaction>",
            "~distaste url <expand " + NICK + "'s to disastisfaction repertoire>",
            "~settings <show current settings>",
            "~update SETTING_NAME value <change a setting>",
            "~roque <start acro game>",
            "~think ABC <come up with an acronym for submitted letters>",
            "~learnword someword <add a word to bot's acronym library>",
            "~boards <show cumulative acronym game scores>",
            "~reload <reload libraries>",
            "~reboot <guess>",
        ]

        for command in list:
            self.say(command)




