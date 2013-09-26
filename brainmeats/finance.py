import simplejson
import locale

from autonomic import axon, category, help, Dendrite
from util import pageopen, Stock


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

        # I feel like this try shouldn't be necessary,
        # something may have changed in the API
        showit = False
        try:
            stock = Stock(symbol)
            showit = stock.showquote(self.context)
        except:
            pass

        if not showit:
            self.chat("Couldn't find company.")
            return

        self.chat(showit)

    @axon
    @help("<get current Bitcoin trading information>")
    def btc(self):
        url = 'https://btc-e.com/api/2/btc_usd/ticker'

        response = pageopen(url)
        if not response:
            self.chat("Couldn't retrieve BTC data.")
            return

        try:
            json = simplejson.loads(response)
        except:
            self.chat("Couldn't parse BTC data.")
            return

        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        last = locale.currency(json['ticker']['last'])
        low = locale.currency(json['ticker']['low'])
        high = locale.currency(json['ticker']['high'])

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
