import mechanize
import urllib
import threading
import re
import time

from collections import OrderedDict
from util import colorize, shorten, pageopen


# TODO?: interface with addlive
class Butler(object):
    maxtasks = 8
    cx = False
    semaphore = False

    def __init__(self, cortex):
        self.cx = cortex
        self.semaphore = threading.BoundedSemaphore(self.maxtasks)
        return

    def wrap(self, func, args, semaphore, note, pid):
        results = func(*args)
        if results:
            note = note % results

        self.cx.chat(note)
        semaphore.release()
        return

    def do(self, func, args, note=False):

        pid = 'task-%s' % time.time()
        self.semaphore.acquire()
        thread = threading.Thread(target=self.wrap, args=(func, args, self.semaphore, note, pid))
        thread.start()


# Better browser through technology
class Browser(object):

    url = False
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'
    ieua = 'User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)'
    robot = mechanize.Browser()
    text = False
    error = False

    def __init__(self, url, params={}, method='GET', userpass=False):
        self.url = url

        self.robot.set_handle_equiv(True)
        self.robot.set_handle_gzip(True)
        self.robot.set_handle_redirect(True)
        self.robot.set_handle_referer(True)
        self.robot.set_handle_robots(False)
        self.robot.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        self.robot.addheaders = [
            ('User-Agent', self.ua),
            ('Accept', '*/*'),
            ('Accept-Encoding', 'gzip,deflate,sdch'),
            ('Accept-Language', 'en-US,en;q=0.8'),
            ('Cache-Control', 'max-age=0'),
            ('Connection', 'keep-alive'),
        ]

        if userpass:
            user, password = userpass.split(':')
            self.robot.add_password(url, user, password)

        try:
            if params:
                data = urllib.urlencode(params)

            if params and method == 'GET':
                self.response = self.robot.open(url + '?%s' % data)
            elif params and method == 'POST':
                self.response = self.robot.open(url, data)
            else:
                self.response = self.robot.open(url)

        except Exception as e:
            self.error = str(e)

    def read(self):
        return self.response.read()

    def title(self):
        try:
            result = self.robot.title().decode('utf-8')
        except Exception as e:
            result = str(e)

        return result

    def headers(self):
        return self.response.info()


# For all your stock needs
class Broker(object):

    def __init__(self, symbol):

        self.stock = None
        self.symbol = symbol
        self.price = 0

        if not symbol:
            return

        # Yahoo uses hyphens in the symbols; old portfolios might be saved
        # with dots from when we were using the Google API - look up with hyphen.
        symbol.replace('.', '-')

        # yahoo fields
        # See http://www.gummy-stuff.org/Yahoo-data.htm for more
        fields = OrderedDict([
            ('symbol', 's'),
            ('price', 'k1'),
            ('perc_change', 'k2'),
            ('change', 'c6'),
            ('exchange', 'x'),
            ('company', 'n'),
            ('volume', 'v'),
            ('market_cap', 'j1'),
        ])

        # yahoo specific
        url = 'http://finance.yahoo.com/d/quotes.csv'
        params = {'f': ''.join(fields.values()), 's': symbol}

        try:
            # TODO: replace pageopen w/ browse
            raw_string = pageopen(url, params).text
            raw_list = raw_string.strip().replace('"', '').split(',')
            data = {key: raw_list.pop(0) for (key) in fields.keys()}
        except Exception as e:
            print e
            return

        if data['exchange'] == 'N/A':
            return

        # Turn N/A - <b>92.73</b> into just the decimal
        data['price'] = float(re.search('(\d|\.)+',
                              data['price'].split('-').pop()).group())
        # Turn N/A - +0.84% into just the decimal
        data['perc_change'] = float(re.search('(\+|-)?(\d|\.)+',
                                    data['perc_change'].split('-').pop()).group())
        data['change'] = float(data['change'])

        for key, value in data.items():
            setattr(self, key, value)

        self.stock = data

    def __nonzero__(self):
        return self.stock is not None

    def showquote(self, context):
        if not self.stock:
            return False

        name = "%s (%s)" % (self.company, self.symbol)
        changestring = str(self.change) + " (" + ("%.2f" % self.perc_change) + "%)"

        if self.change < 0:
            changestring = colorize(changestring, 'red')
        else:
            changestring = colorize(changestring, 'lightgreen')

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

        # TODO: Don't do this for not in channel, ensure it's a privmsg only. Currently not compatible with channeling
        #if context != CHANNEL:
        #    for item in otherinfo:
        #        pretty, id = item
        #        addon = pretty + ": " + getattr(self, id, 'N/A')
        #        message.append(addon)

        link = 'http://finance.yahoo.com/q?s=' + self.symbol
        roasted = shorten(link)
        message.append(roasted)

        output = ', '.join(message)

        return output


