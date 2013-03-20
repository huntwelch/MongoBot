import simplejson
import locale

from autonomic import axon, category, help, Dendrite
from datastore import Drinker, Position
from datetime import datetime
from stocks import Stock
from util import pageopen

#"f":[
#    "~portfolio [stock symbol]<add stock to your portfolio>",
#    "~portfolio <show your portfolio>",
#    "~portfolio clear <empty your portfolio>",
#],


VALID_EXCHANGES = frozenset(['NYSE', 'NYSEARCA', 'NYSEAMEX', 'NASDAQ'])


@category("finance")
class Finance(Dendrite):
    def __init__(self, cortex):
        super(Finance, self).__init__(cortex)

    @axon
    @help("STOCK_SYMBOL <get stock quote>")
    def q(self):
        symbol = self.values[0]

        if not symbol:
            self.chat("Enter a symbol")
            return

        stock = Stock(symbol)
        showit = stock.showquote(self.context)

        if not showit:
            self.chat("Couldn't find company.")
            return

        self.chat(showit)

    @axon
    @help("[QUANTITY] [STOCK_SYMBOL] <buy QUANTITY shares of the stock>")
    def buy(self):
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

        stock = Stock(symbol)

        if not stock:
            self.chat("Stock not found")
            return

        if stock.exchange.upper() not in VALID_EXCHANGES:
            self.chat("Stock exchange %s DENIED!" % stock.exchange)
            return

        drinker = Drinker.objects(name=whom).first()
        if not drinker:
            drinker = Drinker(name=whom)

        cost = stock.price * quantity

        if cost > drinker.cash:
            self.chat("You is poor")
            return

        position = Position(symbol=stock.symbol,
                            price=stock.price,
                            quantity=quantity,
                            date=datetime.utcnow())

        drinker.portfolio.append(position)
        drinker.cash -= cost
        drinker.save()

        self.chat("%s bought %d shares of %s at %s" %\
                (whom, position.quantity, position.symbol, position.price))

    @axon
    @help("[QUANTITY] [STOCK_SYMBOL] <sell QUANTITY shares of the stock>")
    def sell(self):
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

        stock = Stock(symbol)

        if not stock:
            self.chat("Stock not found")
            return

        drinker = Drinker.objects(name=whom).first()
        if not drinker:
            self.chat("You don't have anything to sell")
            return

        check = []
        keep = []
        for p in drinker.portfolio:
            if p.symbol == stock.symbol:
                check.append(p)
            else:
                keep.append(p)

        if not check:
            self.chat("You don't own %s" % stock.symbol)
            return

        check.sort(key=lambda x: x.date)

        for p in check:
            if quantity <= 0:
                keep.append(p)
                continue

            q = min(quantity, p.quantity)

            basis = p.price * q
            value = stock.price * q
            drinker.cash += value

            quantity -= q
            p.quantity -= q
            if p.quantity > 0:
                keep.append(p)

            self.chat("%s sold %d shares of %s at %s (net: %.02f)" % \
                    (whom, q, stock.symbol, stock.price, value-basis))

        drinker.portfolio = keep
        drinker.save()

    @axon
    @help("<show cash money>")
    def cashmoney(self):
        whom = self.lastsender
        drinker = Drinker.objects(name=whom).first()
        if not drinker:
            drinker = Drinker(name=whom)

        self.chat("You gots $%.02f" % drinker.cash)

    @axon
    @help("[STOCK_SYMBOL|clear] <show/add stock to/clear your portfolio>")
    def portfolio(self):
        whom = self.lastsender
        drinker = Drinker.objects(name=whom).first()
        if not drinker:
            self.chat("You don't exist")
            return

        if not drinker.portfolio:
            self.chat("You don't have one")
        else:
            drinker.portfolio.sort(key=lambda p: p.symbol)

            total = 0
            for p in drinker.portfolio:
                self.chat("%10s %10d %10.02f" % (p.symbol, p.quantity, p.price))
                total += p.price
            self.chat("%10s %10s %10s" % ('-' * 10, '-' * 10, '-' * 10))
            self.chat("%10s %10s %10.02f" % ('', '', total))

    @axon
    @help("<get current Bitcoin trading information>")
    def btc(self):
        url = 'https://mtgox.com/api/1/BTCUSD/ticker'

        response = pageopen(url)
        if not response:
            self.chat("Couldn't retrieve BTC data.")
            return

        try:
            json = simplejson.loads(response)
        except:
            self.chat("Couldn't parse BTC data.")
            return

        last = json['return']['last_all']['display_short']
        low = json['return']['low']['display_short']
        high = json['return']['high']['display_short']

        self.chat('Bitcoin, Last: %s, Low: %s, High: %s' % (last, low, high))

    @axon
    @help("<get current Litecoin trading information>")
    def ltc(self):
        url = 'https://btc-e.com/api/2/ltc_usd/ticker'

        response = pageopen(url)
        if not response:
            self.chat("Couldn't retrieve LTC data.")
            return

        try:
            json = simplejson.loads(response)
        except:
            self.chat("Couldn't parse LTC data.")
            return

        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        last = locale.currency(json['ticker']['last'])
        low = locale.currency(json['ticker']['low'])
        high = locale.currency(json['ticker']['high'])

        self.chat('Litecoin, Last: %s, Low: %s, High: %s' % (last, low, high))
