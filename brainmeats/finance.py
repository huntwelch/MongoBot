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
            return str(e)
            pass

        if not showit:
            showit = "Couldn't find company: " + symbol

        return showit

    
    @axon
    @help("<get current Ethereum trading information>")
    def eth(self):
        url = 'https://ethereumprice.org/wp-content/themes/theme/inc/exchanges/price-data.php?coin=eth&cur=ethusd&ex=waex&dec=2'
        
        request = Browser(url)
        if not request:
            return "Couldn't retrieve ETH data."
        
        try:
            json = request.json()
        except:
            return "Couldn't parse ETH data."
        
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        last = locale.currency(float(json['current_price']))
        low = locale.currency(float(json['today_low']))
        high = locale.currency(float(json['today_high']))
        
        if self.values:
            try:
                value = locale.currency(float(json['current_price']) * float(self.values[0]))
            except:
                return "Couldn't compute ETH value."

            return 'Value of %s ETH is %s' % (self.values[0], value)
        else:
            return 'Ethereum, Last: %s, Low: %s, High: %s' % (last, low, high)


    @axon
    @help("<get current Ethereum Classic trading information>")
    def etc(self):
        url = 'https://www.cryptocompare.com/api/data/coinsnapshot/?fsym=ETC&tsym=USD'
        
        request = Browser(url)
        if not request:
            return "Couldn't retrieve ETC data."
        
        try:
            json = request.json()
        except:
            return "Couldn't parse ETC data."
        
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        last = locale.currency(float(json['Data']['AggregatedData']['PRICE']))
        low = locale.currency(float(json['Data']['AggregatedData']['LOW24HOUR']))
        high = locale.currency(float(json['Data']['AggregatedData']['HIGH24HOUR']))
        
        if self.values:
            try:
                value = locale.currency(float(json['Data']['AggregatedData']['PRICE']) * float(self.values[0]))
            except:
                return "Couldn't compute ETC value."

            return 'Value of %s ETC is %s' % (self.values[0], value)
        else:
            return 'Ethereum Classic, Last: %s, Low: %s, High: %s' % (last, low, high)


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

        gdax = '(No result)'
        gdax_url = 'https://api.gdax.com/products/BTC-USD/ticker'
        g_request = Browser(gdax_url)
        try:
            g_json = g_request.json()
            gdax = '$%.2f' % float(g_json['price'])
            if self.values:
                gdax = locale.currency(float(g_json['price']) * float(self.values[0]))
        except:
            pass

        if self.values:
            try:
                value = locale.currency(float(json['ticker']['last']) * float(self.values[0]))
            except:
                return "Couldn't compute BTC value."

            return 'Value of %s BTC is %s, GDAX: %s' % (self.values[0], value, gdax)
        else:
            return 'Bitcoin, Last: %s, Low: %s, High: %s, GDAX: %s' % (last, low, high, gdax)


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
