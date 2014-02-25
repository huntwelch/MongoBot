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
import os
import subprocess

from PIL import Image
from bisect import bisect
from Queue import Queue

from settings import CHANNEL, SHORTENER
from secrets import HTTP_PASS, DELICIOUS_USER, DELICIOUS_PASS
from collections import OrderedDict


# For onetime stuff
totp = pyotp.TOTP(base64.b32encode(HTTP_PASS), interval=600)


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

    return "\x03" + str(color) + ' ' + text + "\x03"


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
    short_url = pageopen(SHORTENER, params={'roast': url})

    if short_url:
        return short_url.text
    return ''


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

        if context != CHANNEL:
            for item in otherinfo:
                pretty, id = item
                addon = pretty + ": " + getattr(self, id, 'N/A')
                message.append(addon)

        link = 'http://finance.yahoo.com/q?s=' + self.symbol
        roasted = shorten(link)
        message.append(roasted)

        output = ', '.join(message)

        return output


def postdelicious(url, title, sender):

    deli = "https://api.del.icio.us/v1/posts/add"
    params = {
        "url": url,
        "description": title,
        "tags": "%s,%s" % (CHANNEL, sender),
    }

    if DELICIOUS_USER:
        auth = requests.auth.HTTPBasicAuth(DELICIOUS_USER, DELICIOUS_PASS)
        try:
            send = requests.get(deli, params=params, auth=auth)
        except:
            pass
            

# http://stevendkay.wordpress.com/2009/09/08/generating-ascii-art-from-photographs-in-python/
# Couldn't have done this with the above link,
# but there are some problems with the script:
# if you adapt from it, don't use 'str' as a 
# variable name unless you want some troubling
# error messages when you try to debug by casting
# exceptions with str(), and im = im.thumbnail
# modifies the original and returns None, so im 
# is no longer usable.
def asciiart(image_path):
    if image_path.find('/') != -1:
        return

    greyscale = [" "," ",".,-","_ivc=!/|\\~","gjez2]/(YL)t[+T7Vf","mdK4ZGbNDXY5P*Q","W8KMA","#%$"]
    zonebounds=[36,72,108,144,180,216,252]
    size = 30
    out = ""

    img = Image.open(image_path)
    img.thumbnail((size, size), Image.ANTIALIAS)
    img = img.resize((size*2, size))
    img = img.convert("L")

    for y in range(0,img.size[1]):
        for x in range(0,img.size[0]):
            lum = 255 - img.getpixel((x,y))
            row = bisect(zonebounds,lum)
            possibles = greyscale[row]
            out += possibles[random.randint(0,len(possibles)-1)]
        out += "\n"

    return out


# TODO?: interface with addlive
class Butler(object):

    cx = False
    
    def __init__(self, cortex):
        self.cx = cortex
        return    
    
    def wrap(self, func, args, note, pid):
        results = func(*args)
        if results:
            note = note % results

        self.cx.chat(note)
        
    def do(self, note, func, args):
        pid = 'task-%s' % time.time() 
        thread = threading.Thread(target=self.wrap, args=(func, args, note, pid))
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


def savefromweb(url, path):
    r = requests.get(url, stream=True)

    if r.status_code != 200:
        return

    with open(path, 'w+') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
        f.close()
