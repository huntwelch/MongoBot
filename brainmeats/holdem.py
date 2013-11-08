import hand
import math
import random
import sys

from autonomic import axon, category, help, Dendrite
from datastore import Drinker


class Player(object):

    def __init__(self, name, money):
        self.name = name
        self.money = money
        self.hand = []
        self.besthand = None
        self.winlimit = None
        self.status = "in"
        self.round_money = 0
        self.hand_money = 0

    def __repr__(self):
        r = "Player(name=%r, money=%r, round_money=%r, hand_money=%r, "\
            "status=%r, hand=%r, winlimit=%r, besthand=%r)" % \
            (self.name, self.money, self.round_money, self.hand_money,
             self.status, self.hand, self.winlimit, self.besthand)
        return r

    def bet(self, money):
        self.money -= money
        self.round_money += money
        self.hand_money += money

    def reset(self):
        self.winlimit = None
        self.besthand = None
        self.round_money = 0
        self.hand_money = 0
        self.hand = []


@category("holdem")
class Holdem(Dendrite):
    def __init__(self, cortex):
        super(Holdem, self).__init__(cortex)

        self.firstpassed = None
        self.lastraised = None
        self.blind = 1
        self.littleblind = None
        self.bigblind = None
        self.cardpointer = 0
        self.playerpointer = 0
        self.players = {}
        self.burncards = []
        self.pot = 0
        self.bet = 0
        self.hand = []
        self.playingholdem = False

        self.stages = (
            'blind',
            'bet',  # set player pointer to left of dealer at each bet phase
            'flop',
            'bet',
            'turn',
            'bet',
            'river',
            'bet',
            'distribute',  # move dealer
        )

        self.stage = 0

    @axon
    @help("STARTING_FUNDS PLAYER_1 PLAYER_2 ... [PLAYER_N] <start holdem game>")
    def holdem(self):
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
            self.players[player] = Player(player, self.stake)

        self._suits = ['s', 'h', 'd', 'c']
        self.suits = (u'\u2660', u'\u2665', u'\u2666', u'\u2663')
        self.ordinal = ('2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A')
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
        self._set_status("sitout")

    @axon
    @help("<resume playing>")
    def sitin(self):
        self._set_status("waiting")

    def _set_status(self, status):
        player = self.lastsender
        if player not in self.players:
            self.announce("You ain't in this game, pardner")
            return

        self.players[player].status = status

    @axon
    @help("AMOUNT <raise the bet by [amount]>")
    def raiseit(self):

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

        if amount <= 0:
            self.announce("That's not money")
            return

        amount += self.bet

        difference = amount - self.players[player].round_money

        if difference > self.players[player].money:
            self.announce("You don't have enough money")
            return
        elif difference == self.players[player].money:
            self.allin()
            return

        self.pot += difference
        self.players[player].bet(difference)
        self.lastraised = player
        self.firstpassed = None

        if self.bet == 0:
            message = player + " bets " + str(amount) + ". "
        if amount == self.bet:
            message = player + " calls. "
        elif amount > self.bet:
            message = player + " raises the bet to " + str(amount) + ". "

        self.bet = amount
        self.turn(prepend=message)

    @axon
    @help("<match the current bet>")
    def callit(self):

        player = self.lastsender
        if player != self.order[self.playerpointer]:
            self.chat("Not your turn")
            return

        difference = self.bet - self.players[player].round_money

        if difference == 0:
            return self.knock()

        if difference > self.players[player].money:
            self.announce("You don't have enough money")
            return

        self.pot += difference
        self.players[player].bet(difference)

        if self.players[player].money == 0:
            self.players[player].status = "allin"

        message = player + " calls. "

        self.turn(prepend=message)

    @axon
    @help("<show how much money you have>")
    def mymoney(self):
        self.chat(str(self.players[self.lastsender].money))

    @axon
    @help("<show how much money everybody has>")
    def allmoney(self):
        for player, p in self.players.iteritems():
            self.chat("%s: %d, %s" % (player, p.money, p.status))
            print p

    @axon
    @help("<pass>")
    def knock(self):

        player = self.lastsender

        if player != self.order[self.playerpointer]:
            self.chat("Not your turn")
            return

        # feels a little awkward, but it's logical.
        if self.bet == self.blind * 2 and player == self.bigblind:
            self.lastraised = self.bigblind
            self.bigblind = None
            self.littleblind = None
            self.announce("%s passes." % player)
            self.turn(jump=0)
            return

        difference = self.bet - self.players[player].round_money

        if difference > 0:
            self.announce("You can't pass.")
            return

        if not self.firstpassed:
            self.firstpassed = player

        message = player + " passes. "
        self.turn(prepend=message)

    @axon
    @help("<you can probably figure this one out>")
    def fold(self):

        player = self.lastsender
        if player != self.order[self.playerpointer]:
            self.chat("Not your turn.")
            return

        self.players[player].status = "folded"
        message = player + " folds. "

        remaining = 0
        for player in self.players:
            if self.players[player].status in ("in", "allin"):
                remaining += 1
                lastman = player

        if remaining == 1:
            self.distribute(lastman)
        else:
            self.turn(prepend=message)

    @axon
    @help("<go all in>")
    def allin(self):

        player = self.lastsender
        if player != self.order[self.playerpointer]:
            self.chat("Not your turn")
            return

        money = self.players[player].money + self.players[player].round_money
        difference = self.bet - self.players[player].round_money
        if self.bet < money:
            self.bet = money

        self.pot += self.players[player].money
        self.players[player].bet(self.players[player].money)
        self.players[player].status = "allin"

        # see if it was actually a raise
        if difference > 0:
            self.lastraised = player
            self.firstpassed = None

        message = player + " goes all in. "

        self.turn(prepend=message)

    @axon
    @help("<show the current bet amount>")
    def thebet(self):
        self.chat("Bet is " + str(self.bet))

    @axon
    @help("<show the amount in the pot>")
    def thepot(self):
        self.chat("Pot is " + str(self.pot))

    def turn(self, jump=1, prepend=""):
        start = self.playerpointer

        self.playerpointer += jump
        self.playerpointer = self.playerpointer % len(self.players)

        # This is a bit convoluted, but it's trying to determine if everyone
        # has had a chance to play.  If we go all the way around the table
        # without finding anyone 'in', we still move to the next round.  That
        # means no one is 'in' or only one person is 'in'.

        in_count = len([p for p in self.players.itervalues()
                       if p.status == "in"])

        if in_count > 1:
            next_round = False
            while True:
                player = self.order[self.playerpointer]

                if player in (self.lastraised, self.firstpassed):
                    next_round = True

                if self.players[player].status == "in":
                    break

                self.playerpointer = (self.playerpointer + 1) % len(self.players)

                if start == self.playerpointer:
                    next_round = True
                    break
        else:
            next_round = True

        if next_round:
            self.announce(prepend)

            self.firstpassed = None
            self.lastraised = None

            stillin = 0
            for p in self.players.itervalues():
                if p.status in ("in", "allin"):
                    stillin += 1

            potbuffer = 0
            for p in self.players.itervalues():
                if p.status == "allin" and p.money <= self.bet:
                    #p.winlimit = self.pot + p.money * stillin
                    p.winlimit = p.hand_money * stillin
                    potbuffer += p.money
                    p.money = 0

                if p.status == "allin" and p.money > self.bet:
                    p.money -= self.bet
                    p.status = "in"
                    potbuffer += self.bet

            self.pot += potbuffer

            for p in self.players.itervalues():
                p.round_money = 0

            self.stage += 1
            self.checkround()
        else:
            player = self.order[self.playerpointer]
            self.announce(prepend + player + "'s turn.")

    def deal(self):

        self.bet = 0
        self.pot = 0
        self.burncards = []
        self.stage = 0
        self.cardpointer = 0
        self.hand = []

        for p in self.players.itervalues():
            p.reset()

        self.dealer = (self.dealer + 1) % len(self.players)
        self.playerpointer = self.dealer

        random.shuffle(self.cards)

        for card in range(2):
            for p in self.players.itervalues():
                if p.status not in ["sitout", "done"]:
                    p.status = "in"
                    p.hand.append(self.cards[self.cardpointer])
                    self.cardpointer += 1

        # handle initial states here
        for player, p in self.players.iteritems():
            self.chat(" ".join(p.hand), player)

        self.pot = self.blind * 3
        self.bet = self.blind * 2

        self.littleblind = self.order[(self.dealer + 1) % len(self.players)]
        self.bigblind = self.order[(self.dealer + 2) % len(self.players)]

        self.players[self.littleblind].bet(self.blind)
        self.players[self.bigblind].bet(self.blind * 2)

        message = self.littleblind + " puts in little blind for " + str(self.blind) + ", "
        message += self.bigblind + " puts in big blind for " + str(self.blind * 2) + ". "

        self.stage = 1

        self.turn(jump=3, prepend=message)

        return

    def nextbet(self, type=""):
        self.announce(type + ": " + " ".join(self.hand))
        self.bet = 0
        self.lastraised = None
        self.firstpassed = None
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

    def distribute(self, lastman=None, side=False):

        if lastman:
            self.players[lastman].money += self.pot
            self.announce("%s takes pot of %d because everyone else folded." %
                          (lastman, self.pot))
        else:
            contenders = []
            for player, p in self.players.iteritems():
                if p.status in ("in", "allin"):
                    self.announce("%s: %s" % (player, " ".join(p.hand)))
                    cardstock = self.translator("".join(p.hand) + "".join(self.hand))
                    (hand_type, besthand, kicker) = hand.find_best_hand(cardstock)
                    p.besthand = besthand
                    contenders.append((hand_type, besthand, kicker, player))

            winners = hand.find_winners(contenders)

            if len(winners) == 1:
                winner = winners[0]
                p = self.players[winner]

                # Decode it because the card object encodes it and so does
                # announce.
                handstr = (' '.join(str(c) for c in p.besthand)).decode('utf-8')

                if not p.winlimit or p.winlimit >= self.pot:
                    p.money += self.pot
                    pot_type = ' side' if side else ''
                    self.announce("%s wins%s pot of %d with a %s" %
                                  (winner, pot_type, self.pot, handstr))
                else:
                    p.money += p.winlimit
                    p.status = "waiting"
                    self.pot -= p.winlimit
                    self.announce("%s wins main pot of %d with a %s" %
                                  (winner, p.winlimit, handstr))

                    if self.pot > 0:
                        self.distribute(side=True)
                        return
            else:
                self.announce("Split pot ...")
                for winner in winners:
                    p = self.players[winner]
                    if p.winlimit:
                        amount = math.floor(p.winlimit / len(winners))
                        p.money += math.floor(p.winlimit / len(winners))
                        p.status = "waiting"
                        self.pot -= p.winlimit
                        self.announce(winner + " takes " + str(amount))
                        self.distribute()
                        return

                amount = math.floor(self.pot / len(winners))
                for winner in winners:
                    p = self.players[winner]
                    p.money += amount
                    self.pot -= amount
                    self.announce(winner + " takes " + str(amount))

        left = 0
        last = None
        players_to_pop = []
        for player, p in self.players.iteritems():
            if p.money == 0:
                p.status = "done"
                self.announce(player + " is out.")
                self.order.remove(player)
                players_to_pop.append(player)
            else:
                left += 1
                last = player

        for player in players_to_pop:
            self.players.pop(player)

        if self.burncards:
            self.announce("Burn cards were: %s" % " ".join(self.burncards))

        if left == 1:
            self.announce("Game over, bitches. Bow to " + last)
            self.playingholdem = False
        else:
            self.deal()
