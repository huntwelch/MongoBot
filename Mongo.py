#!/usr/bin/python

import sys 
import socket 
import string 
import simplejson as json
import os
import random
import threading
import urllib2
import urllib
from time import *
from settings import *

class Mongo:

    def __init__(self):
        
        self.sock = socket.socket( )
        self.sock.connect((HOST, PORT))
        self.sock.send('NICK '+NICK+'\n')
        self.sock.send('USER '+IDENT+' '+HOST+' bla :'+REALNAME+'\n')
        self.sock.send('JOIN '+CHANNELINIT+'\n')

        self.acro_active = False
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
                if self.acro_active:
                    content = line.split(' ',3)

                    if content[2] == NICK:
                        self.game_entry(content)

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
  
        if self.acro_active:
            self.say("Already a game in progress")
            return

        if not self.values or len(self.values) < MIN_PLAYERS:
            self.say("Please select at least " + str(MIN_PLAYERS) + " players")
            return
                   
        self.acro_record = ACROSCORE + strftime('%Y-%m-%d-%H%M')
        open(self.acro_record ,'w')
        self.acro_players = self.values
        self.acro_active = True
        self.acro = Acro(self)
        self.acro.start()

    def game_entry(self,message):
        sender = message[0][1:].split('!')[0]
        entry = message[3][1:]

        if sender not in self.acro_players:
            return

        if self.acro.acro_submit:

            entries = 0

            for line in open(self.acro_record):
                current,subber,timed,what = line.split(":",3)

                if int(current) == self.acro.acro_round:
                    entries += 1
                if int(current) == self.acro.acro_round and sender == subber:
                    return

            TIME = int(mktime(localtime()) - self.acro.acro_mark)
            er = str(self.acro.acro_round) + ":" + sender + ":" + str(TIME) + ":" + entry + "\n"
            open(self.acro_record,'a').write(er)
            numplayers = len(self.acro_players)
            received = entries + 1

            if received == numplayers:
                self.acro.acro_submit = False
                self.acro.acro_voting = True
            else:
                self.say("Entry recieved at " + str(TIME) + " seconds. " + str(numplayers - received) + " more to go.") 

        elif self.acro.acro_voting:

            try:
                vote = int(entry)
            except:
                return 

            self.acro.voters.append(sender)
            self.acro.contenders[vote-1]["votes"] += 1


    def logit(self,what):
        open(LOG,'a').write(what)

    def parse(self,msg):
        info,content = msg[1:].split(':',1)
        sender,type,room = info.strip().split()
        nick = sender.split('!')[0]
        ip = sender.split('@')[1]
    
        if content.find(NICK + " sucks") != -1:
            self.say(sender + "'s MOM sucks")

        if content[:1] == "~":
            self.command(nick,content)
     
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

class Acro(threading.Thread):
    
    def __init__(self,mongo):
        threading.Thread.__init__(self)
        self.mongo = mongo
    
    def gimper(self,check,action,penalty):

        insults = [
            "little bitches",
            "chumps",
        ]
       
        gimps = []
        for player in self.mongo.acro_players:
            if player not in check:
                gimps.append(player)

        if gimps:
            trail = 0
            target = ""
            plural = ""
            for gimp in gimps:
                post = ""
                if trail == 1:
                    plural = "es"
                    post = " and "
                elif trail > 1:
                    post = ", "

                target = gimp + post + target
                if target in self.gimps:
                    self.gimps[target] += penalty
                else:
                    self.gimps[target] = penalty
                        
                trail += 1

            self.mongo.say(target + " are " + random.choice(insults) + " and will be docked " + str(penalty) + " points for not " + action + ".")
                    
    def run(self):
 

        # TODO: make sure all players are present

        self.acro_round = 1
        self.acro_start = mktime(localtime())
        self.acro_mark = mktime(localtime())
        self.warned = False
        self.acro_wait = True
        self.acro_submit = False
        self.acro_voting = False
        self.acro_displayed = False
        self.voters = []
        self.gimps = {}

        self.mongo.say("New game commencing in " + str(BREAK) + " seconds")

        while True:
            self.acro_current = mktime(localtime())

            if self.acro_wait:
                if self.acro_current > self.acro_mark + BREAK:
                    self.acro_wait = False

                    letters = []
                    for line in open(BRAIN + "/letters"):
                        addition = line.split()
                        addition.pop()
                        letters.extend(addition)

                    acronym = ""
                    length = random.randint(MINLEN,MAXLEN)
                    for i in range(1,length):
                        acronym = acronym + random.choice(letters).upper()

                    self.acro_submit = True
                    self.acro_mark = mktime(localtime())
                    self.mongo.say("Round " + str(self.acro_round) + " commencing! Acronym is " + acronym)
                    continue

            if self.acro_submit:

                # check for total answers

                if self.acro_current > self.acro_mark + ROUNDTIME - WARNING and not self.warned:
                    self.warned = True
                    self.mongo.say(str(WARNING) + " seconds left...")
                    continue

                if self.acro_current > self.acro_mark + ROUNDTIME:
                    self.acro_submit = False
                    self.warned = False
                    self.mongo.say("Round over, sluts. Here are the contenders:")

                    # print responses

                    self.contenders = []

                    item = 1
                    submitters = []
                    for line in open(self.mongo.acro_record):
                        r,s,t,c = line.split(":",3)
                        if int(r) == self.acro_round:
                            submitters.append(s)
                            self.contenders.append({
                                "player":s,
                                "time":t,
                                "entry":c.strip(),
                                "votes":0,
                            })
                            self.mongo.say(str(item) + ": " + c)
                        item += 1

                    self.gimper(submitters,"submitting",NO_ACRO_PENALTY)

                    self.mongo.say("You have " + str(VOTETIME) + " seconds to vote.")
                    self.acro_mark = mktime(localtime())
                    self.acro_voting = True
                    continue

            if self.acro_voting:

                # check for full votes

                if self.acro_current > self.acro_mark + VOTETIME:
                    self.acro_voting = False
                    self.mongo.say("Votes are in. The results:")
                            
                    for r in self.contenders:
                        if r['votes'] == 0:
                            note = "dick."
                        elif r['votes'] == 1:
                            note = "1 vote."
                        else:
                            note = str(r['votes']) + " votes."

                        self.mongo.say(r['player'] + "'s \"" + r['entry'] + "\" got " + note)

                    self.gimper(self.voters,"voting",NO_VOTE_PENALTY)

                    # calculate voting and time scores
                    
                    results = {}
                    for player in self.mongo.acro_players:
                        results[player] = {"score":0,"votes":0,"timebonus":0}
                        if player in self.gimps:
                            results[player]["score"] -= self.gimps[player]
                        
                    for r in self.contenders:
                        if r['votes'] != 0:
                            results[r['player']]['score'] += r['votes'] * 10 
                            results[r['player']]['votes'] = r['votes']
                            # TODO
                            timebonus = int((ROUNDTIME/2 - int(r['time']))/TIME_FACTOR)
                            results[r['player']]['timebonus'] = timebonus
                            results[r['player']]['score'] += timebonus

                    for result in results:
                        sc = results[result]
                        word = "bonus"
                        if sc['timebonus'] < 0:
                            word = "penalty"
                        self.mongo.say(result + " came in with " + str(sc['score']) + " with a time " + word + " of " + str(sc['timebonus']) + ".") 

                    # record in game tally

                    if self.acro_round == ROUNDS:
                        # calculate victor have battle vs. war

                        # clear data
                        self.contenders = []
                        self.voters = []

                        # shut 'er down
                        self.mongo.say("Game over.")
                        self.mongo.acro_active = False
                        return

                    self.acro_mark = mktime(localtime())
                    self.mongo.say("Next round in " + str(BREAK) + " seconds.")
                    self.acro_round += 1
                    self.acro_wait = True
                    continue
         
connect = Mongo()
