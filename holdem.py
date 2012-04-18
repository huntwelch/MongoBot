# Le holdem game

import string
import sys
import random
import threading
from time import *
from settings import *


class Holdem(threading.Thread):

    def __init__(self, mongo):
        threading.Thread.__init__(self)
        self.mongo = mongo

    def run(self):

        self.stake = self.mongo.values.pop(0)
        self.blind = 1
        self.order = self.mongo.values
        self.cardpointer = 0
        self.playerpointer = 0
        self.players = {}
        self.pot = 0
        self.bet = 0
        self.lastraised = False
        self.hand = ""

        self.stages = [
            'blind',
            'bet', # set player pointer to left of dealer at each bet phase
            'flop',
            'bet',
            'turn',
            'bet',
            'river',
            'bet',
            'distribute', # move dealer
        ]

        self.stage = 0

        random.shuffle(self.order)  
        self.dealer = 0
        
        for player in self.order:
            self.players[player] = {
                "money": int(self.stake),
                "hand": [],
                "stake": 0,
                "status": "in",  # in,folded,sitout,waiting
            }
        
        self.suits = ['s','h','d','c']
        self._suits = [u'\u2660',u'\u2661',u'\u2662',u'\u2663']
        # find with self.ordinal.index[what]
        self.ordinal = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        self.cards = [] 

        for suit in self.suits:
            for ordinal in self.ordinal:
                self.cards.append(ordinal + suit)

        self.deal()

        while True:
            if self.stages[self.stage] == 'flop':
                self.flop()
                continue

            if self.stages[self.stage] == 'turn':
                self.turncard()
                continue

            if self.stages[self.stage] == 'river':
                self.river()
                continue

            if self.stages[self.stage] == 'distribute':
                self.distribute()
                continue
        
    # player actions

    # note this only happens at the beginning 
    # of each betting phase. maybe combine 
    # with raiseit
    def firstbet(self):

        # validate player turn

        player = self.mongo.lastsender
        
        try:
            money = self.mongo.values[0]
            amount = int(money) 
        except:
            self.mongo.announce("That's not money")
            return
                        
        if amount > self.players[player]["money"]:
            self.mongo.announce("You don't have enough money")
            return
        
        self.bet = amount
        self.pot += amount
        self.lastraised = player
        self.players[player]["money"] -= amount

        self.mongo.announce(player + " raises the bet to " + str(amount))

        self.turn()

        return


    def callit(self):

        player = self.mongo.lastsender

        if self.bet > self.players[player]["money"]:
            self.mongo.announce("You don't have enough money")
            return

        self.pot += self.bet 
        self.players[player]["money"] -= self.bet 

        self.mongo.announce(player + " calls")

        self.turn()

        return

    def status(self):
        for player in self.players:
            self.mongo.chat(str(self.players[player]["money"]) + ", " + self.players[player]["status"])


    def raiseit(self):

        player = self.mongo.lastsender

        try:
            money = self.mongo.values[0]
            amount = int(money) 
        except:
            self.mongo.announce("That's not money")
            return
                        
        amount += self.bet
        if amount > self.players[player]["money"]:
            self.mongo.announce("You don't have enough money")
            return
        
        self.bet = amount
        self.pot += amount
        self.lastraised = player
        self.players[player]["money"] -= amount

        self.mongo.announce(player + " raises the bet to " + str(amount))

        self.turn()

        return


    def knock(self):

        player = self.mongo.lastsender

        if self.bet != 0 and player != self.lastraised: 
            self.mongo.announce("You can't pass.")
            return

        self.mongo.announce(player + " passes.")

        self.turn()

        return


    def fold(self):

        player = self.mongo.lastsender

        self.players[player]["status"] = "folded"
        self.mongo.announce(player + " folds.")

        remaining = 0
        for player in self.players:
            if self.players[player]["status"] == "in":
                remaining += 1
                lastman = player

        if remaining == 1:
            self.distribute(lastman)
            return

        self.turn()

        return


    def allin(self):

        player = self.mongo.lastsender

        # side pot calc

        if self.bet < self.players[player]["money"]:
            self.bet = self.players[player]["money"]
        
        self.pot = self.players[player]["money"]
        self.players[player]["money"] = 0

        self.mongo.announce(player + " goes all in.")

        return


    def turn(self,jump = False):

        self.playerpointer += jump or 1
        self.playerpointer = self.playerpointer % len(self.players)
        
        while self.players[self.order[self.playerpointer]]["status"] != "in":
            self.playerpointer += 1
            self.playerpointer = self.playerpointer % len(self.players)

        player = self.order[self.playerpointer]

        if player == self.lastraised:
            self.stage += 1
            return

        self.mongo.announce(player + "'s turn.")
        return


    def _player(self,offset = 0):
        return self.players[self.order[self.playerpointer + offset]]
        

    def deal(self):
        self.cardpointer = 0
        random.shuffle(self.cards)

        for card in range(2):
            for player in self.players:
                if self.players[player]["status"] != "sitout":
                    self.players[player]["status"] = "in"            
                    self.players[player]["hand"].append(self.cards[self.cardpointer])
                    self.cardpointer += 1

        # handle initial states here
        for player in self.players:
            self.mongo.chat(" ".join(self.players[player]["hand"]), player)

        self.pot = self.blind + self.blind*2
        self._player(1)["money"] -= self.blind
        self._player(2)["money"] -= self.blind*2

        self.stage = 1

        self.turn(3)

        return


    def showpot(self):
        self.mongo.chat("Pot is " + str(self.pot))


    def nextbet(self):
        self.mongo.announce(self.hand)
        self.bet = 0
        self.lastraised = False
        self.playerpointer = self.dealer
        self.stage += 1
        self.turn()
 
    
    def flop(self):
        for card in range(3):
            self.hand += self.cards[self.cardpointer]
            self.cardpointer += 1
        self.nextbet()


    def turncard(self):
        self.hand += self.cards[self.cardpointer]
        self.cardpointer += 1
        self.nextbet()


    def river(self):
        self.hand += self.cards[self.cardpointer]
        self.cardpointer += 1
        self.nextbet()


    def distribute(self,lastman = False):

        # sort out pots
        # increment dealer
        # remove losers
        # reset pot
        # reset bet
        # deal

        self.mongo.announce("Well, you got through a round. Happy fucking birthday, slacker.")

        # change stage

        return

