from __future__ import print_function
import mechanize
import urllib
import threading
import re
import time
import json

from bs4 import BeautifulSoup as bs4
from collections import OrderedDict
from util import colorize, shorten


# Because where would Batman be without Alfred? Without tea,
# that's fucking where. These are handy helper objects for
# dealing with commands and some more complex shit that
# shouldn't be as complex as it ends up being in brainmeats.
# In particular, the Browser object gets around a lot of
# annoyances in http calls.

# This is how we pseudo-thread all the commands.
class Butler(object):
    maxtasks = 8
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


# Better browsing through technology
class Browser(object):

    url = False
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'
    ieua = 'User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)'
    robot = mechanize.Browser()
    text = False
    error = False

    def __init__(self, url, params={}, method='GET', userpass=False, headers=[]):
        self.url = url

        self.robot.set_handle_equiv(True)
        self.robot.set_handle_gzip(True)
        self.robot.set_handle_redirect(True)
        self.robot.set_handle_referer(True)
        self.robot.set_handle_robots(False)
        self.robot.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)


        baseheaders = [
            ('User-Agent', self.ua),
            ('Accept', '*/*'),
            ('Accept-Encoding', 'gzip,deflate,sdch'),
            ('Accept-Language', 'en-US,en;q=0.8'),
            ('Cache-Control', 'max-age=0'),
            ('Connection', 'keep-alive'),
        ]

        self.robot.addheaders = baseheaders + headers

        if userpass:
            user, password = userpass.split(':')
            self.robot.add_password(url, user, password)

        # TODO params are broken
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

    def soup(self):
        return bs4(self.response.read())

    def json(self):
        return json.loads(self.response.read())

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
        symbol = symbol.replace('.', '-')

        # yahoo specific
        url = 'https://api.iextrading.com/1.0/stock/%s/quote' % symbol

        try:
            fulldata = Browser(url).json()
        except Exception as e:
            print(e)
            return

        data = fulldata

        for key, value in data.items():
            setattr(self, key, value)

        self.stock = data

    def __nonzero__(self):
        return self.stock is not None

    def showquote(self, context):

        if not self.stock:
            return False

        name = "%s (%s)" % (self.companyName, self.symbol.upper())
        changestring = str(self.change) + " (" + ("%.2f" % self.changePercent) + "%)"

        if self.change < 0:
            changestring = colorize(changestring, 'red')
        else:
            changestring = colorize(changestring, 'lightgreen')

        message = [
            name,
            str(self.iexRealtimePrice),
            changestring,
        ]

        link = 'http://finance.yahoo.com/q?s=' + self.symbol
        roasted = shorten(link)
        message.append(roasted)

        output = ', '.join(message)

        return output
