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
        self.turn = False  # set to player

        random.shuffle(self.order)

        for player in self.order:
            self.players[player] = {
                "money": int(self.stake),
                "hand": [],
                "stake": 0,
                "status": "in",  # in,folded,sitout,waiting
            }

        # self.suits = ['s','h','d','c']
        self.suits = [u'\u2660', u'\u2661', u'\u2662', u'\u2663']
        # find with self.ordinal.index[what]
        self.ordinal = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.cards = []

        for suit in self.suits:
            for ordinal in self.ordinal:
                self.cards.append(ordinal + suit)

        self.deal()

        while True:
            # process game state
            continue

    # player actions

    def bet(self):
        return

    def callit(self):
        return

    def raiseit(self):
        return

    def knock(self):
        return

    def fold(self):
        return

    def allin(self):
        return

    def setup(self):
        # enter blinds
        # increment turn
        # set dealer
        # pop player and append or something
        # clear hands
        return

    def turn(self, jump=0):
        return

    def deal(self):
        self.cardpointer = 0
        random.shuffle(self.cards)

        for card in range(2):
            for player in self.players:
                self.players[player]["hand"].append(self.cards[self.cardpointer])
                self.cardpointer += 1

        for player in self.players:
            self.mongo.chat(" ".join(self.players[player]["hand"]), player)

        # self.pot = blind + blind*2
        # self.turn(2)

        return
