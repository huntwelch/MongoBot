import urllib
import urllib2
import re
import htmlentitydefs
from settings import CHANNEL, SHORTENER
from xml.dom import minidom as dom


# Utility functions

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text
    return re.sub("&#?\w+;", fixup, text)


# instead of presuming to predict what
# will be colored, make it easy to prep
# string elements
def colorize(text, color):
    colors = {
        "white": 0,
        "black": 1,
        "blue": 2,
        "green": 3,
        "red": 4,
        "brown": 5,
        "purple": 6,
        "orange": 7,
        "yellow": 8,
        "lightgreen": 9,
        "teal": 10,
        "lightcyan": 11,
        "lightblue": 12,
        "pink": 13,
        "grey": 14,
        "lightgrey": 15,
    }
    if isinstance(color, str):
        color = colors[color]

    return "\x03" + str(color) + text + "\x03"



def pageopen(url):
    try:
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urlbase = opener.open(url).read()
        urlbase = re.sub('\s+', ' ', urlbase).strip()
    except:
        return False

    return urlbase


# Utility classes

class Stock(object):

    def __init__(self, symbol):

        self.stock = None
        self.symbol = symbol
        self.price = 0

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

    def __nonzero__(self):
        return self.stock is not None

    # Extracts from google api
    def extract(self, raw):

        elements = raw.childNodes[0].childNodes[0].childNodes

        # in the future, can just change translation
        # point is to end up with an object that won't
        # change when the api changes.

        translation = {
            "symbol": "symbol",
            "pretty_symbol": "pretty_symbol",
            "symbol_lookup_url": "symbol_lookup_url",
            "company": "company",
            "exchange": "exchange",
            "exchange_timezone": "exchange_timezone",
            "exchange_utc_offset": "exchange_utc_offset",
            "exchange_closing": "exchange_closing",
            "divisor": "divisor",
            "currency": "currency",
            "last": "_last",
            "high": "high",
            "low": "low",
            "volume": "volume",
            "avg_volume": "avg_volume",
            "market_cap": "market_cap",
            "open": "open",
            "y_close": "y_close",
            "change": "_change",
            "perc_change": "_perc_change",
            "delay": "delay",
            "trade_timestamp": "trade_timestamp",
            "trade_date_utc": "trade_date_utc",
            "trade_time_utc": "trade_time_utc",
            "current_date_utc": "current_date_utc",
            "current_time_utc": "current_time_utc",
            "symbol_url": "symbol_url",
            "chart_url": "chart_url",
            "disclaimer_url": "disclaimer_url",
            "ecn_url": "ecn_url",
            "isld_last": "isld_last",
            "isld_trade_date_utc": "isld_trade_date_utc",
            "isld_trade_time_utc": "isld_trade_time_utc",
            "brut_last": "brut_last",
            "brut_trade_date_utc": "brut_trade_date_utc",
            "brut_trade_time_utc": "brut_trade_time_utc",
            "daylight_savings": "daylight_savings",
        }
        extracted = {}

        for e in elements:
            data = e.getAttribute("data")
            extracted[translation[e.tagName]] = data
            setattr(self, translation[e.tagName], data)

        if not self.company:
            return None

        self.price = float(self._last)
        try:
            self.change = float(self._change)
            self.perc_change = float(self._perc_change)
        except:
            self.change = 0
            self.perc_change = 0

        # Check for after hours

        self.afterhours = False
        time = int(self.current_time_utc)
        if self.isld_last and (time < 133000 or time > 200000):
            self.afterhours = True
            self.price = float(self.isld_last)
            self.change = self.price - float(self._last)
            self.perc_change = (self.change / float(self._last)) * 100

        return extracted

    def showquote(self, context):
        if not self.stock:
            return False

        name = "%s (%s)" % (self.company, self.symbol)
        changestring = str(self.change) + " (" + ("%.2f" % self.perc_change) + "%)"

        if self.change < 0:
            color = "4"
        else:
            color = "3"

        changestring = "\x03" + color + " " + changestring + "\x03"

        message = [
            name,
            str(self.price),
            changestring,
        ]

        otherinfo = [
            # ("pretty title", "dataname")
            ("Exchange", "exchange"),
            ("Trading volume", "volume"),
            ("Market cap", "market_cap"),
        ]

        if context != CHANNEL:
            for item in otherinfo:
                pretty, id = item
                addon = pretty + ": " + self.stock[id]
                message.append(addon)

        link = urllib.quote("http://www.google.com/finance?client=ig&q=" + self.stock["symbol"])
        try:
            opener = urllib2.build_opener()
            roasted = opener.open(SHORTENER + link).read()
            message.append(roasted)
        except:
            message.append("Can't link")
            

        output = ', '.join(message)
        if self.afterhours:
            output = "After hours: " + output

        return output
