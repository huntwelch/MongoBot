import time
import re
import HTMLParser
import requests
import mechanize
import pyotp
import urllib
import base64
import random
import threading
import subprocess

from PIL import Image
from bisect import bisect
from config import load_config

#from settings import CHANNEL, SHORTENER, THUMBS, THUMB_SIZE, WEBSITE
#from secrets import HTTP_PASS, DELICIOUS_USER, DELICIOUS_PASS
from collections import OrderedDict

from pprint import pprint

settings = load_config('config/settings.yaml') 
secrets = load_config('config/secrets.yaml') 


# For onetime stuff
totp = pyotp.TOTP(base64.b32encode(secrets.webserver.password), interval=600)


# Utility functions


# http://stackoverflow.com/questions/667508/whats-a-good-rate-limiting-algorithm
def ratelimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)

    def decorate(func):
        lastTimeCalled = [0.0]

        def rateLimitedFunction(*args, **kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait > 0:
                time.sleep(leftToWait)
            ret = func(*args, **kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate


def unescape(text):
    parser = HTMLParser.HTMLParser()
    return parser.unescape(text)


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

    return "\x03" + str(color) + text + "\x03\x0f"


class Browse(object):

    url = False
    ua = '(Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36'
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


HEADERS = {'User-agent': '(Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36' }

def pageopen(url, params={}):
    try:
        urlbase = requests.get(url, headers=HEADERS, params=params, timeout=5)
    except requests.exceptions.RequestException as e:
        print e
        return False
    except:
        return False

    return urlbase


def shorten(url):
    # TODO uhg needs to be a class that knows it's specifc to roa.st
    #short_url = pageopen(SHORTENER, params={'roast': url})

    #if short_url:
    #    return short_url.text
    return url


# Utility classes
class Stock(object):

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
            raw_string = pageopen(url, params).text
            raw_list = raw_string.strip().replace('"', '').split(',')
            data = {key: raw_list.pop(0) for (key) in fields.keys()}
        except Exception as e:
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
            changestring = colorize(changestring, 'green')

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


def postdelicious(url, title, sender):
    # TODO Just commenting this all out since we don't want to make this use config; should be a brainmeat
    #deli = "https://api.del.icio.us/v1/posts/add"
    #params = {
    #    "url": url,
    #    "description": title,
    #    "tags": "%s,%s" % (CHANNEL, sender),
    #}

    #if DELICIOUS_USER:
    #    auth = requests.auth.HTTPBasicAuth(DELICIOUS_USER, DELICIOUS_PASS)
    #    try:
    #        send = requests.get(deli, params=params, auth=auth)
    #    except:
    #        pass
    pass


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


def savevideo(url, path):
    args = [
        'youtube-dl',
        '--restrict-filenames',
        url,
        '-o',
        path,
    ]

    # Save output from the real run in
    # for error checks. Someday.
    feedback = subprocess.check_output(args)

    # Simulated run to get the file name.
    # Though it pops more proc, there are
    # some advantages to this: simple parsing
    # and handles the already downloaded
    # error while still being useful.
    filename = False
    args.append('--get-filename')
    filename = subprocess.check_output(args)

    return filename.strip()


# Use of 'thumber' var is crappy, but probably
# moving this to a Browse method, so not worrying
# about it right now.
def savefromweb(url, path, thumber=False):
    # TODO could be a receptor that can also get called with a specific url attached to it
    # TODO deprecate function in favor of Browse. Note dependencies
    r = requests.get(url, stream=True, verify=False)


    if r.status_code != 200:
        return

    with open(path, 'w+') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
        f.close()

    # TODO this qualifies as either its own method or an artsy method
    #if thumber:
    #    fname = "%s_%s.jpeg" % ( thumber, int(time.mktime(time.localtime())) )
    #    img = Image.open(path)
    #    img.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.ANTIALIAS)
    #    img.save('server%s%s' % (THUMBS, fname))
    #    return '%s%s%s' % (WEBSITE, THUMBS, fname)
    pass


import random
import string 

zalgochars = [
    [
        u'\u030d',       u'\u030e',       u'\u0304',       u'\u0305',
        u'\u033f',       u'\u0311',       u'\u0306',       u'\u0310', 
        u'\u0352',       u'\u0357',       u'\u0351',       u'\u0307', 
        u'\u0308',       u'\u030a',       u'\u0342',       u'\u0343', 
        u'\u0344',       u'\u034a',       u'\u034b',       u'\u034c', 
        u'\u0303',       u'\u0302',       u'\u030c',       u'\u0350', 
        u'\u0300',       u'\u0301',       u'\u030b',       u'\u030f', 
        u'\u0312',       u'\u0313',       u'\u0314',       u'\u033d', 
        u'\u0309',       u'\u0363',       u'\u0364',       u'\u0365', 
        u'\u0366',       u'\u0367',       u'\u0368',       u'\u0369',
        u'\u036a',       u'\u036b',       u'\u036c',       u'\u036d',
        u'\u036e',       u'\u036f',       u'\u033e',       u'\u035b',
        u'\u0346',       u'\u031a' 
    ],
    
    [
        u'\u0E47' 
    ],
    
    [
        u'\u0316',       u'\u0317',       u'\u0318',       u'\u0319', 
        u'\u031c',       u'\u031d',       u'\u031e',       u'\u031f', 
        u'\u0320',       u'\u0324',       u'\u0325',       u'\u0326',
        u'\u0329',       u'\u032a',       u'\u032b',       u'\u032c',
        u'\u032d',       u'\u032e',       u'\u032f',       u'\u0330',
        u'\u0331',       u'\u0332',       u'\u0333',       u'\u0339',
        u'\u033a',       u'\u033b',       u'\u033c',       u'\u0345',
        u'\u0347',       u'\u0348',       u'\u0349',       u'\u034d', 
        u'\u034e',       u'\u0353',       u'\u0354',       u'\u0355', 
        u'\u0356',       u'\u0359',       u'\u035a',       u'\u0323' 
    ],
    
    [
        u'\u0315',       u'\u031b',       u'\u0340',       u'\u0341', 
        u'\u0358',       u'\u0321',       u'\u0322',       u'\u0327',
        u'\u0328',       u'\u0334',       u'\u0335',       u'\u0336',
        u'\u034f',       u'\u035c',       u'\u035d',       u'\u035e', 
        u'\u035f',       u'\u0360',       u'\u0362',       u'\u0338',
        u'\u0337',       u'\u0361',       u'\u0489'
    ],
]

fears = [
    'HE COMES',
    'they are coming',
    'cannot see',
    'she is glorious',
    'no hope no hope',
    'it rises',
    'no light',
    'no escape',
    'breaking',
    'in my mind',
    'pain',
    'cannot move',
    'nightmares',
    'a room with a moose',
]

# HE COMES
def zalgo(_string):
    if len(_string) < 10:
        return _string

    amount = random.randint(10,len(_string))
    base = _string[:amount]
    zalgoit = list(_string[amount:])
    zalgoed = u''
    while zalgoit:
        # TODO Not sure if all the incessant u''ing is necessary
        char = zalgoit.pop(0)
        zalgoed = u'%s%s' % (zalgoed, char)

        if char == ' ':
            continue
        
        if random.randint(0, 30) == 13:
            fear = ' %s' % random.choice(fears)
            zalgoit = list(fear) + zalgoit
            continue

        direction = random.choice(zalgochars)
        for x in range(0,4): 
            tic = random.choice(direction)
            zalgoed = u'%s%s' % (zalgoed, tic)
        
    return u'%s%s' % (base, zalgoed)
