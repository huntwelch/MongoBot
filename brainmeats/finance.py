import locale

from autonomic import axon, help, Dendrite
from staff import Broker, Browser


# Stock stuff. This is a shockingly complex
# and well maintained part of the bot because
# everyone in my chatroom except yours truly
# has stocks and likes keeping track of them
# and discussing market movements and ...
# shorts and ... zzzzzzzzzzSNORK what? Where
# am ... oh right. Yeah. Here's stock stuff.
class Finance(Dendrite):

    def __init__(self, cortex):
        super(Finance, self).__init__(cortex)


    @axon
    @help("STOCK_SYMBOL <get stock quote>")
    def q(self):
        symbol = self.values[0]
        if not symbol:
            return "Enter a symbol"

        showit = False
        try:
            stock = Broker(symbol)
            showit = stock.showquote(self.context)
        except Exception as e:
            pass

        if not showit:
            showit = "Couldn't find company: " + symbol

        return showit


    @axon
    @help("<get current Bitcoin trading information>")
    def btc(self):
        url = 'https://btc-e.com/api/2/btc_usd/ticker'

        request = Browser(url)
        if not request:
            return "Couldn't retrieve BTC data."

        try:
            json = request.json()
        except:
            return "Couldn't parse BTC data."

        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        last = locale.currency(json['ticker']['last'])
        low = locale.currency(json['ticker']['low'])
        high = locale.currency(json['ticker']['high'])

        if self.values:
            try:
                value = locale.currency(float(json['ticker']['last']) * float(self.values[0]))
            except:
                return "Couldn't compute BTC value."

            return 'Value of %s BTC is %s' % (self.values[0], value)
        else:
            return 'Bitcoin, Last: %s, Low: %s, High: %s' % (last, low, high)


    @axon
    @help("<get current Litecoin trading information>")
    def ltc(self):
        url = 'https://btc-e.com/api/2/ltc_usd/ticker'

        request = Browser(url)
        if not request:
            return "Couldn't retrieve LTC data."

        try:
            json = request.json()
        except:
            return "Couldn't parse LTC data."

        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        last = locale.currency(json['ticker']['last'])
        low = locale.currency(json['ticker']['low'])
        high = locale.currency(json['ticker']['high'])

        if self.values:
            try:
                value = locale.currency(float(json['ticker']['last']) * float(self.values[0]))
            except:
                return "Couldn't compute LTC value."

            return 'Value of %s LTC is %s' % (self.values[0], value)
        else:
            return 'Litecoin, Last: %s, Low: %s, High: %s' % (last, low, high)


    @axon
    @help("<get current Dogecoin trading information>")
    def doge(self):
        url = 'http://dogecoinaverage.com/USD.json'

        request = Browser(url)
        if not request:
            return "Couldn't retrieve DOGE data."

        try:
            json = request.json()
        except:
            return "Couldn't parse DOGE data."

        weighted = float(json['vwap'])

        if self.values:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
                value = locale.currency(weighted * float(self.values[0]))
            except:
                return "Couldn't compute DOGE value."

            return 'Value of %s DOGE is %s' % (self.values[0], value)
        else:
            return 'Dogecoin, Volume-Weighted Average Price: $%s' % (weighted)
