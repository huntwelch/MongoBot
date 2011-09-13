#!/usr/local/bin/python

import sys 
import socket 
import string 
import simplejson as json
import os
import random
import threading
import urllib2
import urllib
from acro import Acro
from time import *
from settings import *

# TODO
# better round time work
# force entries to match acronym (?) what kind of exceptions...
# move arco to imported file
# put insults in imported file

class Mongo:

    def __init__(self):
        
        self.sock = socket.socket( )
        self.sock.connect((HOST, PORT))
        self.sock.send('NICK '+NICK+'\n')
        self.sock.send('USER '+IDENT+' '+HOST+' bla :'+REALNAME+'\n')
        self.sock.send('JOIN '+CHANNELINIT+'\n')

        self.acro = False
        self.values = False

        self.monitor()

    def monitor(self):
        while True:
            line = self.sock.recv(500)
            line = line.strip()
            if line != '':
                self.logit(line + '\n')
        
            if line.find('PING') != -1:
                self.sock.send('PONG ' + line.split()[1] + '\n')
                continue
        
            if line.find('PRIVMSG') != -1:
                if self.acro:
                    content = line.split(' ',3)

                    if content[2] == NICK:
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
    
        {
            "help":self.showlist,    
            "distaste":self.distaste,    
            "reboot":self.reboot,    
            "update":self.update,    
            "acro":self.acroengine,    
            "love":self.love,    
        }.get(what,self.default)()

    # Le Game

    def acroengine(self):
  
        if self.acro:
            self.say("Already a game in progress")
            return

        if not self.values or len(self.values) < MIN_PLAYERS:
            self.say("Please select at least " + str(MIN_PLAYERS) + " players")
            return
                   
        self.acro = Acro(self)
        self.acro.players = self.values
        self.acro.start()

    def logit(self,what):
        open(LOG,'a').write(what)

    def parse(self,msg):
        info,content = msg[1:].split(':',1)
        try:
            sender,type,room = info.strip().split()
        except:
            return

        nick = sender.split('!')[0]
        ip = sender.split('@')[1]
    
        if content.find(NICK + " sucks") != -1:
            self.say(sender + "'s MOM sucks")

        if content[:1] == "~":
            self.command(nick,content)

		if content.find("mom"):
			open(BRAIN + "/mom.log",'a').write(content)
     
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

    def say(self,message):
        self.sock.send('PRIVMSG '+ CHANNELINIT +' :' + message + '\n')

    def default(self):
        self.say(NICK + " cannot do this thing :'(")

    def showlist(self):
        list = [
            "~help <show this message>",
            "~love <command " + NICK + " to love>",
            "~distaste <command " + NICK + " to express disastisfaction>",
            "~distaste url <expand " + NICK + "'s to disastisfaction repertoire>",
            "~update SETTING_NAME value <change a setting>",
            "~acro player_1 ... player_n <start acro game>",
            "~reboot <take a wild flaming guess>",
        ]

        self.say("Commands: " + ', '.join(list))

    def reboot(self):
        sys.exit()

connect = Mongo()
