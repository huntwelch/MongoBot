import urllib2
import urllib
from xml.dom import minidom as dom

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
            return

        self.stock = self.extract(raw)
        
    # Extracts from google model, will fail in october
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

    def showquote(self):

        if not self.stock:
            return False
    
        name = self.stock["company"] + " (" + self.stock["symbol"] + ")" 
        change = self.stock["change"] + " (" + self.stock["perc_change"] + "%)"

        if float(self.stock["change"][:-1]) < 0:
            color = "4" 
        else:
            color = "3" 

        change = "\x03" + color + " " + change + "\x03"

        message = [
            name,
            self.stock["last"],
            change,
        ]

        otherinfo = [
            # ("pretty title", "dataname")
            ("Exchange","exchange"),
            ("Trading volume","volume"),
            ("Market cap","market_cap"),
        ]   

        for item in otherinfo:
            pretty,id = item
            addon = pretty + ": " + self.stock[id]
            message.append(addon)
            
        # this should work even after the api goes down
        link = "http://www.google.com/finance?client=ig&q=" + self.stock["symbol"]
        message.append(link)

        return ', '.join(message)


