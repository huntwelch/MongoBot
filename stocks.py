import urllib
from settings import *
from xml.dom import minidom as dom
from datastore import Drinker

class Stock:

    def __init__(self, symbol):

        self.stock = False

        if not symbol:
            return

        # google specific
        singlestock = "http://www.google.com/ig/api?stock="
        url = singlestock + symbol 

        try:
            raw = dom.parse(urllib.urlopen(url)) 
        except:
            return False

        self.stock = self.extract(raw)
        self.symbol = symbol 
        
    # should be in a Stocks or Portfolio or something class
    def save(self, whom):
        drinker = Drinker.objects(name = whom) 
        if drinker:
            drinker = drinker[0]
            portfolio = drinker.portfolio
            
            if self.symbol in portfolio:
                return
            
            portfolio.append(self.symbol)
            drinker.portfolio = portfolio
        else:
            drinker = Drinker(name = whom, portfolio = [self.symbol])

        drinker.save()


    # Extracts from google api 
    def extract(self, raw):
        
        elements = raw.childNodes[0].childNodes[0].childNodes

        # in the future, can just change translation
        # point is to end up with an object that won't 
        # change when the api changes.

        translation = {
            "symbol":"symbol",
            "pretty_symbol":"pretty_symbol",
            "symbol_lookup_url":"symbol_lookup_url",
            "company":"company",
            "exchange":"exchange",
            "exchange_timezone":"exchange_timezone",
            "exchange_utc_offset":"exchange_utc_offset",
            "exchange_closing":"exchange_closing",
            "divisor":"divisor",
            "currency":"currency",
            "last":"last",
            "high":"high",
            "low":"low",
            "volume":"volume",
            "avg_volume":"avg_volume",
            "market_cap":"market_cap",
            "open":"open",
            "y_close":"y_close",
            "change":"change",
            "perc_change":"perc_change",
            "delay":"delay",
            "trade_timestamp":"trade_timestamp",
            "trade_date_utc":"trade_date_utc",
            "trade_time_utc":"trade_time_utc",
            "current_date_utc":"current_date_utc",
            "current_time_utc":"current_time_utc",
            "symbol_url":"symbol_url",
            "chart_url":"chart_url",
            "disclaimer_url":"disclaimer_url",
            "ecn_url":"ecn_url",
            "isld_last":"isld_last",
            "isld_trade_date_utc":"isld_trade_date_utc",
            "isld_trade_time_utc":"isld_trade_time_utc",
            "brut_last":"brut_last",
            "brut_trade_date_utc":"brut_trade_date_utc",
            "brut_trade_time_utc":"brut_trade_time_utc",
            "daylight_savings":"daylight_savings",
        }
        extracted = {}

        for e in elements:
            extracted[translation[e.tagName]] = e.getAttribute("data")         

        if extracted["company"] == "":
            return False

        return extracted

    def showquote(self,context):

        if not self.stock:
            return False
    
        value = float(self.stock["last"])
        change = float(self.stock["change"])
        perc_change = float(self.stock["perc_change"])

        # Check for after hours

        afterhours = False 
        time = int(self.stock["current_time_utc"])
        if self.stock["isld_last"] and (time < 133000 or time > 200000): 
            afterhours = True
            value = float(self.stock["isld_last"])
            change = value - float(self.stock["last"])
            perc_change = (change / float(self.stock["last"])) * 100

        name = self.stock["company"] + " (" + self.stock["symbol"] + ")" 
        changestring = str(change) + " (" + ("%.2f" % perc_change) + "%)"

        if change < 0:
            color = "4" 
        else:
            color = "3" 

        changestring = "\x03" + color + " " + changestring + "\x03"

        message = [
            name,
            str(value),
            changestring,
        ]

        otherinfo = [
            # ("pretty title", "dataname")
            ("Exchange","exchange"),
            ("Trading volume","volume"),
            ("Market cap","market_cap"),
        ]   

        if context != CHANNEL: 
            for item in otherinfo:
                pretty,id = item
                addon = pretty + ": " + self.stock[id]
                message.append(addon)
            
            # this should work even after the api goes down
            link = "http://www.google.com/finance?client=ig&q=" + self.stock["symbol"]
            message.append(link)

        output = ', '.join(message) 
        if afterhours:
            output = "After hours: " + output 

        return output


