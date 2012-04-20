# Le holdem game

import string
import sys
import random
import threading
import hand
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
        self.burncards = "" 
        self.pot = 0
        self.bet = 0
        self.lastraised = False
        self.hand = ""

        self.stages = [
            'blind',
            'bet',  # set player pointer to left of dealer at each bet phase
            'flop',
            'bet',
            'turn',
            'bet',
            'river',
            'bet',
            'distribute',  # move dealer
        ]

        self.stage = 0

        random.shuffle(self.order)
        self.dealer = 0

        for player in self.order:
            self.players[player] = {
                "money": int(self.stake),
                "hand": [],
                "stake": 0,
                "winlimit": False,
                "status": "in",  # in,folded,sitout,waiting,allin,done
            }

        self.suits = ['s', 'h', 'd', 'c']
        self._suits = [u'\u2660', u'\u2661', u'\u2662', u'\u2663']
        # find with self.ordinal.index[what]
        self.ordinal = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
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

    def sitout(self):
        player = self.mongo.lastsender
        self.players[player]["status"] = "sitout"
        return

    def sitin(self):
        player = self.mongo.lastsender
        self.players[player]["status"] = "waiting"
        return

    def firstbet(self):

        # validate player turn

        player = self.mongo.lastsender
        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return 

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
        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return 

        if self.bet > self.players[player]["money"]:
            self.mongo.announce("You don't have enough money")
            return

        self.pot += self.bet
        self.players[player]["money"] -= self.bet

        self.mongo.announce(player + " calls")

        self.turn()

        return

    def mymoney(self):
        self.chat(self.players[self.mongo.lastsender]["money"])

    def status(self):
        for player in self.players:
            self.mongo.chat(str(self.players[player]["money"]) + ", " + self.players[player]["status"])

    def raiseit(self):

        player = self.mongo.lastsender
        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return 

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
        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return 

        if self.bet != 0 and player != self.lastraised:
            self.mongo.announce("You can't pass.")
            return

        self.mongo.announce(player + " passes.")

        self.turn()

        return

    def fold(self):

        player = self.mongo.lastsender
        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return 

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

    def whatbet(self):
        self.mongo.chat("The bet is " + str(self.bet))
        return

    def allin(self):

        player = self.mongo.lastsender
        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return 

        if self.bet < self.players[player]["money"]:
            self.bet = self.players[player]["money"]

        self.lastraised = player # I think this works...

        self.allins.append({player: self.players[player]["money"]})
        self.players[player]["money"] = 0
        self.players[player]["status"] = "allin"

        self.mongo.announce(player + " goes all in.")

        return

    def turn(self, jump=False):

        self.playerpointer += jump or 1
        self.playerpointer = self.playerpointer % len(self.players)

        # should be right; handles all ins, and last raised
        # should always adhere to reality
        if self.order[self.playerpointer] == self.lastraised:

            stillin = 0
            for player in self.players:
                p = self.players[player]
                if p["status"] == "in" or (p["status"] == "allin" and p["money"] > 0):
                    stillin += 1
                
            potbuffer = 0
            for player in self.players:
                p = self.players[player]
                if p["status"] == "allin" and p["money"] <= self.bet:
                    p["winlimit"] = self.pot + p["money"]*stillin
                    potbuffer += p["money"]
                    p["money"] = 0
                     
                if p["status"] == "allin" and p["money"] > self.bet:
                    p["money"] -= self.bet
                    p["status"] = "in"
                    potbuffer += self.bet                    

            self.pot += potbuffer

            self.stage += 1
            return

        while self.players[self.order[self.playerpointer]]["status"] != "in":
            self.playerpointer += 1
            self.playerpointer = self.playerpointer % len(self.players)

        player = self.order[self.playerpointer]

        self.mongo.announce(player + "'s turn.")
        return

    def _player(self, offset=0):
        return self.players[self.order[self.playerpointer + offset]]

    def deal(self):

        self.bet = 0
        self.pot = 0
        self.burncards = ""
        self.stage = 0
        self.cardpointer = 0

        # increment dealer

        random.shuffle(self.cards)

        for card in range(2):
            for player in self.players:
                p = self.players[player]
                if p["status"] not in ["sitout","done"]:
                    p["status"] = "in"
                    p["winlimit"] = False 
                    p["hand"].append(self.cards[self.cardpointer])
                    self.cardpointer += 1

        # handle initial states here
        for player in self.players:
            self.mongo.chat(" ".join(self.players[player]["hand"]), player)

        self.pot = self.blind + self.blind * 2
        self._player(1)["money"] -= self.blind
        self._player(2)["money"] -= self.blind * 2

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

    def burn(self):
        self.burncards += self.cards[self.cardpointer]
        self.cardpointer += 1
        
    def flop(self):
        self.burn()
        for card in range(3):
            self.hand += self.cards[self.cardpointer]
            self.cardpointer += 1
        self.nextbet()

    def turncard(self):
        self.burn()
        self.hand += self.cards[self.cardpointer]
        self.cardpointer += 1
        self.nextbet()

    def river(self):
        self.burn()
        self.hand += self.cards[self.cardpointer]
        self.cardpointer += 1
        self.nextbet()

    def translator(handstring):
        base = list(handstring)
        handobjects = []

        while len(base):
            ordinal = self.ordinal.index(base.pop(0)) + 1
            suit = self.suits.index(base.pop(0)) + 1
            handobjects.append(hand.card(suit,ordinal))

        return handobjects


    def distribute(self, lastman=False):

        if lastman:
            self.players[lastman]["money"] += self.pot
            self.mongo.announce(lastman + " takes it because everyone else folded.")
            self.deal()
            return

        contenders = []
        reveal = []
        for player in self.players:
            p = self.players[player]
            if p["status"] in ["in","allin"]:
                self.mongo.announce(player + ": " + p["hand"])
                cardstock = self.translator("".join(p["hand"]) + self.hand)
                (hand_type, hand, kicker) = hand.find_best_hand(cardstock) 
                p["besthand"] = hand 
                contenders.append((hand_type, hand, kicker,player))
        
        winners = hand.find_winners(contenders)
        if len(winners) == 1:
            winner = winners[0][3]
            p = self.players[winner]
            if not p["winlimit"]:
                p["money"] += self.pot
                self.mongo.announce(winner + " wins with a " + p["besthand"])
                self.deal()
                return
            else:
                p["money"] += p["winlimit"] 
                p["status"] = "waiting"
                self.pot -= p["winlimit"]
                self.mongo.announce(winner + " wins main pot with a " + p["besthand"])
                self.distribute()
                return
        else:
            self.mongo.announce("Split pot ...")
            for winner in winners:
                p = self.players[winner[3]]
                if p["winlimit"]:
                    amount = math.floor(p["winlimit"]/len(winners))
                    p["money"] += math.floor(p["winlimit"]/len(winners))
                    p["status"] = "waiting"
                    self.pot -= p["winlimit"]
                    self.mongo.announce(winner[3] + " takes " + str(amount))
                    self.distribute()
                    return
            
            amount = math.floor(self.pot/len(winners))
            for winner in winners:
                p = self.players[winner[3]]
                p["money"] += amount
                self.pot -= amount
                self.mongo.announce(winner[3] + " takes " + str(amount))
                                
        left = 0
        last = False
        for player in self.players:
            p = self.players[player]
            if p["money"] == 0:
                p["status"] = "done"
                self.mongo.announce(player + " is out.")
            else:
                left += 1
                last = player 

        if left == 1:
            self.mongo.announce("Game over, bitches. Bow to " + last)
            self.mongo.playingholdem = False
            sys.exit()
            return
        
        self.deal()
        return
          

