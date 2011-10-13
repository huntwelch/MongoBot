# Le acrobot game

import string 
import sys 
import random
import threading
from time import *
from settings import *

class Acro(threading.Thread):
    
    def __init__(self,mongo):
        threading.Thread.__init__(self)
        self.mongo = mongo
    
    def gimper(self,check,action,penalty):
 
        gimps = []
        for player in self.players:
            if player not in check:
                gimps.append(player)

        use = INSULT 

        if gimps:
            trail = 0
            target = ""
            for gimp in gimps:
                post = ""
                if trail == 1:
                    use = INSULTS 
                    post = " and "
                elif trail > 1:
                    post = ", "

                if gimp in self.gimps:
                    self.gimps[gimp] += penalty
                else:
                    self.gimps[gimp] = penalty
                        
                target = gimp + post + target
                trail += 1

            self.mongo.announce(target + " " + random.choice(use) + " and will be docked " + str(penalty) + " points for not " + action + ".")
                    
    def endgame(self):
        # clear data
        self.contenders = []
        self.voters = []

        # shut 'er down
        self.mongo.announce("Game over.")
        self.mongo.acro = False
        self.killgame = False
        self.paused = False
        sys.exit()

    def input(self,message,SelfSub=False):
        if self.paused:
            self.mongo.announce("Game is paused.")
            return

        if not SelfSub:
            sender = message[0][1:].split('!')[0]
            entry = message[3][1:]
        else:
            sender = NICK 
            entry = self.mongo.acronymit(self.currentacronym)

        if sender not in self.players and self.round != 1:
            return

        if self.submit:

            entries = 0

            for line in open(self.record):
                try:
                    current,subber,timed,what = line.split(":",3)
                except:
                    continue

                if int(current) == self.round:
                    entries += 1
                if int(current) == self.round and sender == subber:
                    return

            if not SelfSub:
                TIME = int(mktime(localtime()) - self.mark)
            else:
                TIME = int(ROUNDTIME/2)
            
            words = entry.split()
            temp = []
            for word in words:
                if word[:1] == "-":
                    temp.append(word[1:])
                else:
                    temp.append(word.capitalize())
                    open(BRAIN + "/natwords",'a').write(word.capitalize() + "\n")
            
            entry = ' '.join(temp)

            er = str(self.round) + ":" + sender + ":" + str(TIME) + ":" + entry + "\n"
            open(self.record,'a').write(er)
            numplayers = len(self.players)
            received = entries + 1

            addition = ""
            if self.round != 1:
                addition = str(numplayers - received) + " more to go."

            if not SelfSub:
                self.mongo.announce("Entry recieved at " + str(TIME) + " seconds. " + addition) 

            if received == numplayers and self.round != 1:
                self.bypass = True
            elif self.round == 1: 
                self.players.append(sender)

        elif self.voting:
            if BOTPLAY and NICK not in self.voters:
                self.voters.append(NICK)

            if len(self.players) < MIN_PLAYERS:
                self.mongo.announce("Need at least" + str(MIN_PLAYERS) + " players. Sorry.") 

            try:
                vote = int(entry)
            except:
                return 

            if sender == self.contenders[vote-1]["player"]:
                self.mongo.announce(sender + " tried to vote for himself. What a bitch.")
                return

            try:
                self.contenders[vote-1]["votes"] += 1
                self.voters.append(sender)
                if len(self.voters) == len(self.players):
                    self.bypass = True
            except:
                return

    def run(self):

        self.record = ACROSCORE + strftime('%Y-%m-%d-%H%M') + '.game'
        open(self.record ,'w')
        self.round = 1
        self.cumulative = {}
        self.start = mktime(localtime())
        self.mark = mktime(localtime())
        self.warned = False
        self.wait = True
        self.submit = False
        self.voting = False
        self.bypass = False
        self.displayed = False
        self.voters = []
        self.players = []
        self.gimps = {}
        self.SelfSubbed = False 
        self.paused = False 
        self.killgame = False 

        self.mongo.announce("New game commencing in " + str(BREAK) + " seconds")

        while True:
            if self.killgame:
                self.endgame()

            if self.paused:
                continue

            self.current = mktime(localtime())

            if self.wait:
                if self.current > self.mark + BREAK:
                    self.wait = False

                    letters = []
                    for line in open(BRAIN + "/letters"):
                        addition = line.split()
                        addition.pop()
                        letters.extend(addition)

                    acronym = ""
                    length = random.randint(MINLEN,MAXLEN)
                    for i in range(1,length):
                        acronym = acronym + random.choice(letters).upper()

                    self.currentacronym = acronym
                    self.submit = True
                    self.mark = mktime(localtime())
                    self.mongo.announce("Round " + str(self.round) + " commencing! Acronym is " + acronym)
                    continue

            if self.submit:

                if self.current > self.mark + ROUNDTIME - WARNING and not self.warned:
                    self.warned = True
                    self.mongo.announce(str(WARNING) + " seconds left...")
                    continue

                if BOTPLAY and not self.SelfSubbed:
                    self.input(False,True)
                    self.SelfSubbed = True
                    

                if self.current > self.mark + ROUNDTIME or self.bypass:
                    if self.round == 1:
                        for player in self.players:
                            self.cumulative[player] = 0

                    self.bypass = False
                    self.submit = False
                    self.warned = False
                    self.mongo.announce("Round over, sluts. Here are the contenders:")

                    # print responses

                    self.contenders = []

                    submitters = []
                    for line in open(self.record):
                        try:
                            r,s,t,c = line.split(":",3)
                        except:
                            continue

                        if int(r) == self.round:
                            submitters.append(s)
                            self.contenders.append({
                                "player":s,
                                "time":t,
                                "entry":c.strip(),
                                "votes":0,
                            })
                    
                    random.shuffle(self.contenders)                    
                    item = 1
                    for submission in self.contenders: 
                        self.mongo.announce(str(item) + ": " + submission["entry"])
                        item += 1
                    
                    if not self.contenders:
                        self.mongo.announce("Don't waste my friggin time")
                        sys.exit()
                    
                    if self.round != 1:
                        self.gimper(submitters,"submitting",NO_ACRO_PENALTY)

                    self.mongo.announce("You have " + str(VOTETIME) + " seconds to vote.")
                    self.mark = mktime(localtime())
                    self.voting = True
                    continue

            if self.voting:

                # check for full votes

                if self.current > self.mark + VOTETIME or self.bypass:
                    self.bypass = False
                    self.voting = False
                    self.mongo.announce("Votes are in. The results:")
                            
                    for r in self.contenders:
                        if r['votes'] == 0:
                            note = "dick."
                        elif r['votes'] == 1:
                            note = "1 vote."
                        else:
                            note = str(r['votes']) + " votes."

                        self.mongo.announce(r['player'] + "'s \"" + r['entry'] + "\" got " + note)

                    self.gimper(self.voters,"voting",NO_VOTE_PENALTY)

                    # calculate voting and time scores
                    
                    results = {}
                    for player in self.players:
                        results[player] = {"score":0,"votes":0,"timebonus":0}
                        if player in self.gimps:
                            results[player]["score"] -= self.gimps[player]
                        
                    for r in self.contenders:
                        if r['votes'] != 0:
                            results[r['player']]['score'] += r['votes'] * 10 
                            results[r['player']]['votes'] = r['votes']
                            if int(r['time']) < ROUNDTIME/2:
                                timebonus = int((ROUNDTIME/2 - int(r['time']))/TIME_FACTOR)
                            else:
                                timebonus = 0

                            results[r['player']]['timebonus'] = timebonus
                            results[r['player']]['score'] += timebonus

                    
                    tally = "Round:" + str(self.round) + "\n"  
                    
                    for result in results:
                        sc = results[result]
                        
                        self.cumulative[result] += sc['score']

                        score = str(sc['score'])
                        bonus = str(sc['timebonus'])
                        total = str(self.cumulative[result])

                        self.mongo.announce(result + " came in with " + score + " with a time bonus of " + bonus + ", for a total of " + total) 
                        tally += result + " " + str(sc['score']) + " (" + str(sc['timebonus']) + ")\n"

                    open(self.record,'a').write("\n" + tally + "\n")

                    # record in game tally

                    if self.round == ROUNDS:
                        self.endgame()

                    self.SelfSubbed = False
                    self.voters = []
                    self.contenders = []
                    self.gimps = {}
                    self.mark = mktime(localtime())
                    self.mongo.announce("Next round in " + str(BREAK) + " seconds.")
                    self.round += 1
                    self.wait = True
                    continue
         

