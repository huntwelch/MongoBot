from mongoengine import *

from autonomic import axon, help, Dendrite
from datastore import Drinker, Position
from datetime import datetime
from staff import Broker

from config import load_config
from id import Id


# The stock game, it's awesome. It has stocks. Nice.
class Stockgame(Dendrite):

    def __init__(self, cortex):
        super(Stockgame, self).__init__(cortex)


    # Helper method to create a position
    def _create_position(self, ptype):

        whom = self.lastsender

        try:
            quantity = int(self.values[0])
            symbol = self.values[1]
        except:
            self.chat("That's not right")
            return

        if quantity <= 0:
            self.chat("Do you think this is a muthafuckin game?")
            return

        stock = Broker(symbol)

        if not stock:
            self.chat("Stock not found")
            return

        if stock.exchange.upper() not in self.config.exchanges:
            self.chat("Stock exchange %s DENIED!" % stock.exchange)
            return

        if stock.price < 0.01:
            self.chat("No penny stocks")
            return

        drinker = Id(whom)

        if not drinker.cash:
            drinker.cash = self.config.startupcash

        if not drinker.positions:
            drinker.positions = []

        cost = stock.price * quantity

        if cost > drinker.cash:
            self.chat("You is poor")
            return

        position = Position(symbol=stock.symbol,
                            price=stock.price,
                            quantity=quantity,
                            date=datetime.utcnow(),
                            type=ptype)

        drinker.positions.append(position)
        drinker.cash -= cost
        # drinker.save()

        verb = 'bought' if ptype == 'long' else 'shorted'

        self.chat("%s %s %d shares of %s (%s) at %s" %
                  (drinker.nick, verb, position.quantity, stock.company,
                   position.symbol, position.price))


    def _close_position(self, ptype):

        whom = self.lastsender

        try:
            quantity = int(self.values[0])
            symbol = self.values[1]
        except:
            self.chat("That's not right")
            return

        if quantity <= 0:
            self.chat("Do you think this is a muthafuckin game?")
            return

        stock = Broker(symbol)

        if not stock:
            self.chat("Stock not found")
            return

        drinker = Id(whom)
        if not drinker.is_authenticated:
            self.chat("You don't have a portfolio")
            return

        check = []
        keep = []
        for p in drinker.positions:
            if p.symbol == stock.symbol and p.type == ptype:
                check.append(p)
            else:
                keep.append(p)

        if not check:
            self.chat("I don't see %s in your portfolio" % stock.symbol)
            return

        check.sort(key=lambda x: x.date)

        verb = 'sold' if ptype == 'long' else 'covered'

        for p in check:
            if quantity <= 0:
                keep.append(p)
                continue

            q = min(quantity, p.quantity)

            basis = p.price * q
            value = stock.price * q
            if ptype == 'long':
                drinker.cash += value
                net = value - basis
            else:
                net = basis - value
                drinker.cash += basis + net

            quantity -= q
            p.quantity -= q
            if p.quantity > 0:
                keep.append(p)

            self.chat("%s %s %d shares of %s at %s (net: %.02f)" %
                      (drinker.nick, verb, q, stock.symbol, stock.price, net))

        drinker.positions = keep


    @axon
    @help("QUANTITY STOCK_SYMBOL <buy QUANTITY shares of the stock>")
    def buy(self):
        self._create_position('long')


    @axon
    @help("QUANTITY STOCK_SYMBOL <sell QUANTITY shares of the stock>")
    def sell(self):
        self._close_position('long')


    @axon
    @help("QUANTITY STOCK_SYMBOL <cover QUANTITY shares of the stock>")
    def cover(self):
        self._close_position('short')


    @axon
    @help("QUANTITY STOCK_SYMBOL <short QUANTITY shares of the stock>")
    def short(self):
        self._create_position('short')


    @axon
    @help("<stock scores of players>")
    def stockscore(self):
        if self.values:
            drinkers = Drinker.objects(name__in=self.values)
        else:
            drinkers = Drinker.objects

        scores = []

        for drinker in drinkers:
            # Assume these people are not playing.
            if not drinker.positions and drinker.cash == self.config.startupcash:
                continue

            total = 0
            collateral = 0
            cash = drinker.cash

            for p in drinker.positions:
                stock = Broker(p.symbol)
                if p.type == 'long':
                    net = p.quantity * stock.price
                else:
                    net = -p.quantity * stock.price
                    collateral += 2 * p.quantity * p.price
                if net >= 10000000:
                    # Get rid of stupid twitter positions
                    continue

                total += net

            scores.append((drinker.name, cash, collateral,
                           total, cash + collateral + total))

        if not scores:
            self.chat("can't find 'em, won't find 'em")
        else:
            scores.sort(key=lambda x: x[4], reverse=True)

            self.chat("%15s %10s %10s %10s %10s" %
                      ('drinker', 'cash', 'collateral', 'value', 'total'))
            for s in scores:
                self.chat("%15s %10.02f %10.02f %10.02f %10.02f" % s)


    @axon
    @help("<show cash money>")
    def cashmoney(self):

        whom = self.lastsender

        drinker = Id(whom)

        self.chat("You gots $%.02f" % drinker.cash)


    @axon
    @help("[USERNAME] <show person's portfolio>")
    def portfolio(self):
        if not self.values:
            whom = self.lastsender
        else:
            whom = self.values[0]

        drinker = Id(whom)
        if not drinker.is_recognized:
            self.chat("%s doesn't exist" % whom)
            return

        if not drinker.positions:
            self.chat("%s doesn't have one" % drinker.name)
        else:
            drinker.positions.sort(key=lambda p: p.symbol)

            self.chat("%8s %10s %10s %10s %10s %10s" % ('type', 'symbol',
                      'qty', 'price', 'last', 'gain'))

            total = 0
            for p in drinker.positions:
                stock = Broker(p.symbol)

                if p.type == 'long':
                    net = p.quantity * (stock.price - p.price)
                else:
                    net = p.quantity * (p.price - stock.price)

                if net >= 10000000:
                    # Get rid of stupid twitter positions
                    continue

                self.chat("%8s %10s %10d %10.02f %10.02f %10.02f" %
                          (p.type, p.symbol, p.quantity, p.price, stock.price,
                           net))

                total += net

            self.chat("%8s %10s %10s %10s %10s %10.02f" % ('', '', '', '', '', total))


    @axon
    def clearstockgamepleasedontbeadickaboutthis(self):
        try:
            cash = int(self.values[0])
        except:
            cash = self.config.startupcash

        if self.lastsender == 'sublimnl':
            self.chat("You are why we can't have nice things.")
            return

        for drinker in Drinker.objects:
            drinker.cash = cash
            drinker.positions = []



