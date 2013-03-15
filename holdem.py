# Le holdem game

from settings import *
from time import *
import hand
import math
import random
import sys

# TODO:
# bets don't add up
# blind doesn't register right player
# eternal passing still?

# "h": [
#     "~holdem <start holdem game>",
#     "~bet [amount] <>",
#     "~call <match bet, if able>",
#     "~raise [amount] <raise the bet>",
#     "~pass/~knock/~check  <pass bet>",
#     "~fold <leave hand>",
#     "~allin <bet everything>",
#     "~sitout <leave game temporarily>",
#     "~sitin <rejoin game>",
#     "~status <show all players' money and status>",
#     "~pot <show amount in pot>",
#     "~mymoney <show how much money you have>",
#     "~thebet <show current bet>",
# ],
#
# # Holdem
# "holdem": self.holdemengine,
# "bet": self.holdem.raiseit,
# "call": self.holdem.callit,
# "raise": self.holdem.raiseit,
# "pass": self.holdem.knock,
# "knock": self.holdem.knock,
# "check": self.holdem.knock,
# "fold": self.holdem.fold,
# "allin": self.holdem.allin,
# "sitin": self.holdem.sitin,
# "sitout": self.holdem.sitout,
# "status": self.holdem.status,
# "pot": self.holdem.showpot,
# "mymoney": self.holdem.mymoney,
# "thebet": self.holdem.thebet,

#    # Move to holdem
#    def holdemengine(self):
#        if self.playingholdem:
#            self.chat("Already a game in progress")
#            return
#
#        self.playingholdem = True
#        self.holdem.start()


class Holdem(threading.Thread):

    def __init__(self, mongo):
        threading.Thread.__init__(self)
        self.mongo = mongo

    def run(self):

        try:
            self.stake = int(self.mongo.values.pop(0))
        except:
            self.mongo.announce("First entry must be a number.")
            self.mongo.playingholdem = False
            self.stop()
            sys.exit()

        if len(self.mongo.values) < 2:
            self.mongo.announce("You must have at least two players.")
            self.mongo.playingholdem = False
            self.stop()
            sys.exit()

        self.firstpassed = False
        self.blind = 1
        self.littleblind = False
        self.bigblind = False
        self.order = self.mongo.values
        self.cardpointer = 0
        self.playerpointer = 0
        self.players = {}
        self.burncards = []
        self.pot = 0
        self.bet = 0
        self.lastraised = False
        self.hand = []

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
                "besthand": False,
                "stake": 0,
                "winlimit": False,
                "status": "in",  # in,folded,sitout,waiting,allin,done
            }

        self._suits = ['s', 'h', 'd', 'c']
        self.suits = [u'\u2660', u'\u2665', u'\u2666', u'\u2663']
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

    def sitout(self):
        player = self.mongo.lastsender
        self.players[player]["status"] = "sitout"
        return

    def sitin(self):
        player = self.mongo.lastsender
        if player not in self.players:
            self.mongo.announce("You ain't in this game, pardner")
            return

        self.players[player]["status"] = "waiting"
        return

    def raiseit(self):

        # needs to be higher than bet

        self.firstpassed = False

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

        if amount < self.bet:
            self.mongo.announce("You can't bet less than the current bet.")
            return

        if amount > self.players[player]["money"]:
            self.mongo.announce("You don't have enough money")
            return

        self.pot += amount
        self.lastraised = player
        self.players[player]["money"] -= amount

        if self.bet == 0:
            message = player + " bets " + str(amount) + ". "
        if amount == self.bet:
            message = player + " calls. "
        if amount > self.bet:
            message = player + " raises the bet to " + str(amount) + ". "

        self.bet = amount
        self.turn(False, message)

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

        message = player + " calls. "

        self.turn(False, message)

        return

    def mymoney(self):
        self.mongo.chat(self.players[self.mongo.lastsender]["money"])

    def status(self):
        for player in self.players:
            self.mongo.chat(player + ": " + str(self.players[player]["money"]) + ", " + self.players[player]["status"])

    def knock(self):

        player = self.mongo.lastsender

        # feels a little awkward, but it's logical.
        if self.bet == self.blind * 2 and player == self.bigblind:
            self.bigblind = False
            self.littleblind = False
            message = player + " passes. "
            self.turn(False, message)
            return

        if not self.firstpassed:
            self.firstpassed = player

        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return

        if self.bet != 0 and player != self.lastraised:
            self.mongo.announce("You can't pass.")
            return

        message = player + " passes. "
        self.turn(False, message)
        return

    def fold(self):

        player = self.mongo.lastsender
        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return

        self.players[player]["status"] = "folded"
        message = player + " folds. "

        remaining = 0
        for player in self.players:
            if self.players[player]["status"] in ["in", "allin"]:
                remaining += 1
                lastman = player

        if remaining == 1:
            self.distribute(lastman)
            return

        self.turn(False, message)

        return

    def whatbet(self):
        self.mongo.chat("The bet is " + str(self.bet))
        return

    def allin(self):

        self.firstpassed = False

        player = self.mongo.lastsender
        if player != self.order[self.playerpointer]:
            self.mongo.chat("Not your turn")
            return

        if self.bet < self.players[player]["money"]:
            self.bet = self.players[player]["money"]

        self.lastraised = player  # I think this works...

        self.players[player]["money"] = 0
        self.players[player]["status"] = "allin"

        message = player + " goes all in. "

        self.turn(False, message)

        return

    def turn(self, jump=False, prepend=""):

        self.playerpointer += jump or 1
        self.playerpointer = self.playerpointer % len(self.players)

        while self.players[self.order[self.playerpointer]]["status"] != "in":
            self.playerpointer = (self.playerpointer + 1) % len(self.players)

        if self.order[self.playerpointer] == self.lastraised or self.order[self.playerpointer] == self.firstpassed:

            self.firstpassed = False
            self.lastraised = False

            stillin = 0
            for player in self.players:
                p = self.players[player]
                if p["status"] == "in" or (p["status"] == "allin" and p["money"] > 0):
                    stillin += 1

            potbuffer = 0
            for player in self.players:
                p = self.players[player]
                if p["status"] == "allin" and p["money"] <= self.bet:
                    p["winlimit"] = self.pot + p["money"] * stillin
                    potbuffer += p["money"]
                    p["money"] = 0

                if p["status"] == "allin" and p["money"] > self.bet:
                    p["money"] -= self.bet
                    p["status"] = "in"
                    potbuffer += self.bet

            self.pot += potbuffer

            self.stage += 1
            return

        player = self.order[self.playerpointer]

        self.mongo.announce(prepend + player + "'s turn.")
        return

    def deal(self):

        self.bet = 0
        self.pot = 0
        self.burncards = []
        self.stage = 0
        self.cardpointer = 0
        self.hand = []

        for player in self.players:
            p = self.players[player]
            p["winlimit"] = False
            p["hand"] = []
            p["besthand"] = False

        self.dealer = (self.dealer + 1) % len(self.players)
        self.playerpointer = self.dealer

        random.shuffle(self.cards)

        for card in range(2):
            for player in self.players:
                p = self.players[player]
                if p["status"] not in ["sitout", "done"]:
                    p["status"] = "in"
                    p["hand"].append(self.cards[self.cardpointer])
                    self.cardpointer += 1

        # handle initial states here
        for player in self.players:
            self.mongo.chat(" ".join(self.players[player]["hand"]), player)

        self.pot = self.blind * 3
        self.bet = self.blind * 2

        self.littleblind = self.order[(self.dealer + 1) % len(self.players)]
        self.bigblind = self.order[(self.dealer + 2) % len(self.players)]

        self.players[self.littleblind]["money"] -= self.blind
        self.players[self.bigblind]["money"] -= self.blind * 2

        message = self.littleblind + " puts in little blind for " + str(self.blind) + ", "
        message += self.bigblind + " puts in big blind for " + str(self.blind * 2) + ". "

        self.stage = 1

        self.turn(3, message)

        return

    def thebet(self):
        self.mongo.chat("Bet is " + str(self.bet))

    def showpot(self):
        self.mongo.chat("Pot is " + str(self.pot))

    def nextbet(self, type=""):

        self.mongo.announce(type + ": " + " ".join(self.hand))
        self.bet = 0
        self.lastraised = False
        self.playerpointer = self.dealer
        self.stage += 1
        self.turn()

    def burn(self):
        self.burncards.append(self.cards[self.cardpointer])
        self.cardpointer += 1

    def flop(self):
        self.burn()
        for card in range(3):
            self.hand.append(self.cards[self.cardpointer])
            self.cardpointer += 1
        self.nextbet("Flop")

    def turncard(self):
        self.burn()
        self.hand.append(self.cards[self.cardpointer])
        self.cardpointer += 1
        self.nextbet("Turn")

    def river(self):
        self.burn()
        self.hand.append(self.cards[self.cardpointer])
        self.cardpointer += 1
        self.nextbet("River")

    def translator(self, handstring):
        base = list(handstring)
        handobjects = []

        while len(base):
            self.mongo.chat("".join(base), "chiyou")
            ordinal = self.ordinal.index(base.pop(0)) + 1
            suit = self.suits.index(base.pop(0)) + 1
            handobjects.append(hand.card(suit, ordinal))

        return handobjects

    def distribute(self, lastman=False):

        if lastman:
            self.players[lastman]["money"] += self.pot
            self.mongo.announce(lastman + " takes it because everyone else folded.")
            self.deal()
            return

        contenders = []
        for player in self.players:
            p = self.players[player]
            if p["status"] in ["in", "allin"]:
                self.mongo.announce(player + ": " + " ".join(p["hand"]))
                cardstock = self.translator("".join(p["hand"]) + "".join(self.hand))
                (hand_type, besthand, kicker) = hand.find_best_hand(cardstock)
                p["besthand"] = besthand
                contenders.append((hand_type, besthand, kicker, player))

        winners = hand.find_winners(contenders)
        if len(winners) == 1:
            winner = winners[0]
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
                p = self.players[winner]
                if p["winlimit"]:
                    amount = math.floor(p["winlimit"] / len(winners))
                    p["money"] += math.floor(p["winlimit"] / len(winners))
                    p["status"] = "waiting"
                    self.pot -= p["winlimit"]
                    self.mongo.announce(winner + " takes " + str(amount))
                    self.distribute()
                    return

            amount = math.floor(self.pot / len(winners))
            for winner in winners:
                p = self.players[winner]
                p["money"] += amount
                self.pot -= amount
                self.mongo.announce(winner + " takes " + str(amount))

        left = 0
        last = False
        for player in self.players:
            p = self.players[player]
            if p["money"] == 0:
                p["status"] = "done"
                self.mongo.announce(player + " is out.")
                self.order.remove(player)
                self.players.remove(player)
            else:
                left += 1
                last = player

        self.mongo.announce("Burn cards were: " + " " + " ".join(self.burncards))

        if left == 1:
            self.mongo.announce("Game over, bitches. Bow to " + last)
            self.mongo.playingholdem = False
            sys.exit()
            return

        self.deal()
        return
