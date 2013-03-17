from autonomic import axon, category, help, Dendrite


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

@category("holdem")
class Holdem(Dendrite):
    def __init__(self, cortex):
        super(Holdem, self).__init__(cortex)

        self.firstpassed = False
        self.blind = 1
        self.littleblind = False
        self.bigblind = False
        self.cardpointer = 0
        self.playerpointer = 0
        self.players = {}
        self.burncards = []
        self.pot = 0
        self.bet = 0
        self.lastraised = False
        self.hand = []
        self.playingholdem = False

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

    @axon
    @help("[starting funds] [player_1] ... [player_n] <start holdem game>")
    def holdem(self):
        self.snag()
        if self.playingholdem:
            self.announce("Game already in progress.")
            return

        try:
            self.stake = int(self.values.pop(0))
        except:
            self.announce("First entry must be a number.")
            return

        if len(self.values) < 2:
            self.announce("You must have at least two players.")
            return

        self.playingholdem = True
        self.order = self.values
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

    def checkround(self):
        fn = {
            "flop": self.flop,
            "turn": self.turncard,
            "river": self.river,
            "distribute": self.distribute,
        }.get(self.stages[self.stage])

        if fn:
            fn()

    @axon
    @help("<stop playing>")
    def sitout(self):
        player = self.lastsender
        self.players[player]["status"] = "sitout"
        return

    @axon
    @help("<resume playing>")
    def sitin(self):
        player = self.lastsender
        if player not in self.players:
            self.announce("You ain't in this game, pardner")
            return

        self.players[player]["status"] = "waiting"
        return

    @axon
    @help("[amount] <raise the bet by [amount]>")
    def raiseit(self):

        self.firstpassed = False

        player = self.lastsender
        if player != self.order[self.playerpointer]:
            self.chat("Not your turn")
            return

        try:
            money = self.values[0]
            amount = int(money)
        except:
            self.announce("That's not money")
            return

        amount += self.bet

        if amount > self.players[player]["money"]:
            self.announce("You don't have enough money")
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

    @axon
    @help("<match the current bet>")
    def callit(self):

        player = self.lastsender
        if player != self.order[self.playerpointer]:
            self.chat("Not your turn")
            return

        if self.bet > self.players[player]["money"]:
            self.announce("You don't have enough money")
            return

        self.pot += self.bet
        self.players[player]["money"] -= self.bet

        message = player + " calls. "

        self.turn(False, message)

        return

    @axon
    @help("<show how much money you have>")
    def mymoney(self):
        self.chat(str(self.players[self.lastsender]["money"]))

    @axon
    @help("<show how much money everybody has>")
    def allmoney(self):
        for player in self.players:
            self.chat(player + ": " + str(self.players[player]["money"]) + ", " + self.players[player]["status"])

    @axon
    @help("<pass>")
    def knock(self):

        player = self.lastsender

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
            self.chat("Not your turn")
            return

        if self.bet != 0 and player != self.lastraised:
            self.announce("You can't pass.")
            return

        message = player + " passes. "
        self.turn(False, message)
        return

    @axon
    @help("<you can probably figure this one out>")
    def fold(self):

        player = self.lastsender
        if player != self.order[self.playerpointer]:
            self.chat("Not your turn.")
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

    @axon
    @help("<go all in>")
    def allin(self):

        self.firstpassed = False

        player = self.lastsender
        if player != self.order[self.playerpointer]:
            self.chat("Not your turn")
            return

        if self.bet < self.players[player]["money"]:
            self.bet = self.players[player]["money"]

        self.lastraised = player  # I think this works...

        self.players[player]["money"] = 0
        self.players[player]["status"] = "allin"

        message = player + " goes all in. "

        self.turn(False, message)

        return

    @axon
    @help("<show the current bet amount>")
    def thebet(self):
        self.chat("Bet is " + str(self.bet))

    @axon
    @help("<show the amount in the pot>")
    def thepot(self):
        self.chat("Pot is " + str(self.pot))

    def turn(self, jump=False, prepend=""):
        self.playerpointer += jump or 1
        self.playerpointer = self.playerpointer % len(self.players)

        while self.players[self.order[self.playerpointer]]["status"] != "in":
            self.playerpointer = (self.playerpointer + 1) % len(self.players)

        if self.order[self.playerpointer] in (self.lastraised, self.firstpassed):

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
            self.checkround()
            return

        player = self.order[self.playerpointer]

        self.announce(prepend + player + "'s turn.")

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
            self.chat(" ".join(self.players[player]["hand"]), player)

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

    def nextbet(self, type=""):
        self.announce(type + ": " + " ".join(self.hand))
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
        "Translate the hand string to a list of Card objects."

        base = list(handstring)
        handobjects = []

        while len(base):
            # Account for the 10 card being two characters.
            ordinal = base.pop(0)
            if ordinal == '1':
                base.pop(0)
                ordinal = '10'

            ordinal = self.ordinal.index(ordinal) + 1
            suit = self.suits.index(base.pop(0)) + 1
            handobjects.append(hand.Card(suit, ordinal))

        return handobjects

    def distribute(self, lastman=False):

        if lastman:
            self.players[lastman]["money"] += self.pot
            self.announce(lastman + " takes it because everyone else folded.")
            self.deal()
            return

        contenders = []
        for player in self.players:
            p = self.players[player]
            if p["status"] in ["in", "allin"]:
                self.announce(player + ": " + " ".join(p["hand"]))
                cardstock = self.translator("".join(p["hand"]) + "".join(self.hand))
                (hand_type, besthand, kicker) = hand.find_best_hand(cardstock)
                p["besthand"] = besthand
                contenders.append((hand_type, besthand, kicker, player))

        winners = hand.find_winners(contenders)
        if len(winners) == 1:
            winner = winners[0]
            p = self.players[winner]

            # Decode it because the card object encodes it and so does
            # announce.
            handstr = str(p["besthand"]).decode('utf-8')

            if not p["winlimit"]:
                p["money"] += self.pot
                self.announce("%s wins with a %s" % (winner, handstr))
            else:
                p["money"] += p["winlimit"]
                p["status"] = "waiting"
                self.pot -= p["winlimit"]
                self.announce("%s wins main pot with a %s" % (winner, handstr))
                self.distribute()
                return
        else:
            self.announce("Split pot ...")
            for winner in winners:
                p = self.players[winner]
                if p["winlimit"]:
                    amount = math.floor(p["winlimit"] / len(winners))
                    p["money"] += math.floor(p["winlimit"] / len(winners))
                    p["status"] = "waiting"
                    self.pot -= p["winlimit"]
                    self.announce(winner + " takes " + str(amount))
                    self.distribute()
                    return

            amount = math.floor(self.pot / len(winners))
            for winner in winners:
                p = self.players[winner]
                p["money"] += amount
                self.pot -= amount
                self.announce(winner + " takes " + str(amount))

        left = 0
        last = False
        players_to_pop = []
        for player in self.players:
            p = self.players[player]
            if p["money"] == 0:
                p["status"] = "done"
                self.announce(player + " is out.")
                self.order.remove(player)
                players_to_pop.append(player)
            else:
                left += 1
                last = player

        for player in players_to_pop:
            self.players.pop(player)

        self.announce("Burn cards were: " + " " + " ".join(self.burncards))

        if left == 1:
            self.announce("Game over, bitches. Bow to " + last)
            self.playingholdem = False
        else:
            self.deal()
