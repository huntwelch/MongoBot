import HTMLParser
import re
import simplejson
import textwrap
import urllib

from autonomic import axon, alias, category, help, Dendrite
from BeautifulSoup import BeautifulSoup
from settings import REPO, NICK, SAFE
from secrets import WEATHER_API
from util import pageopen


@category("reference")
class Reference(Dendrite):
    def __init__(self, cortex):
        super(Reference, self).__init__(cortex)

        self.safe_calc = dict([(k, locals().get(k, f)) for k, f in SAFE])

    @axon
    @help("SEARCH_TERM <look something up in google>")
    def g(self):
        if not self.values:
            self.chat("Enter a word")
            return

        query = "+".join(self.values)
        url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=large&q=%s&start=0" % (query)

        # Google no likey pageopen func
        try:
            results = urllib.urlopen(url)
            json = simplejson.loads(results.read())
        except:
            self.chat("Something's buggered up")
            return

        if json["responseStatus"] != 200:
            self.chat("Bad status")
            return

        result = json["responseData"]["results"][0]
        title = result["titleNoFormatting"]
        link = result["url"]

        self.chat(title + " @ " + link)

    @axon
    @help("<display link to bot's github repository>")
    def source(self):
        self.chat(REPO)

    @axon
    @help("ZIP_CODE <get weather>")
    def weather(self):
        if not WEATHER_API:
            self.chat("WEATHER_API is not set")
            return

        if not self.values or not re.search("^\d{5}", self.values[0]):
            self.chat("Please enter a zip code.")
            return

        zip = self.values[0]
        url = "http://api.wunderground.com/api/%s/conditions/q/%s.json" % (WEATHER_API, zip)

        response = pageopen(url)
        if not response:
            self.chat("Couldn't get weather.")
            return

        try:
            json = simplejson.loads(response)
        except:
            self.chat("Couldn't parse weather.")
            return

        json = json['current_observation']

        location = json['display_location']['full']
        condition = json['weather']
        temp = json['temperature_string']
        humid = json['relative_humidity']
        wind = json['wind_string']
        feels = json['feelslike_string']

        base = "%s, %s, %s, Humidity: %s, Wind: %s, Feels like: %s"
        self.chat(base % (location, condition, temp, humid, wind, feels))

    @axon
    @alias(["urban"])
    @help("SEARCH_TERM <get urban dictionary entry>")
    def ud(self):
        if not self.values:
            self.chat("Whatchu wanna know, bitch?")
            return

        term = ' '.join(self.values)

        query = urllib.urlencode({'term': term})
        url = 'http://www.urbandictionary.com/define.php?%s' % query
        urlbase = pageopen(url)

        try:
            soup = BeautifulSoup(urlbase,
                                 convertEntities=BeautifulSoup.HTML_ENTITIES)
        except:
            self.chat("parse error")
            return

        defn = []

        elem = soup.find('div', {'class': 'definition'})
        if elem:
            if elem.string:
                defn = [elem.string]
            elif elem.contents:
                defn = []
                for c in elem.contents:
                    if c.string and c.string.strip():
                        defn.append(c.string.strip())

        if defn:
            # Unfortunately, BeautifulSoup doesn't parse hexadecimal HTML
            # entities like &#x27; so use the parser for any stray entities.
            parser = HTMLParser.HTMLParser()

            for paragraph in defn:
                wrapped = textwrap.wrap(paragraph, 80)
                for line in wrapped:
                    self.chat(parser.unescape(line))
        else:
            self.chat("couldn't find anything")


    # This function used to be called calc, but was changed to hack in
    # honor of Ken's incredibly sick exploitation of the eval function, 
    # which gave him direct access to the database:
    # (lambda f=(lambda n:[c for c in ().__class__.__bases__[0].__subclasses__() 
    # if c.__name__=='catch_warnings'][0]()._module.__builtins__[n]): 
    # f("eval")(f("compile")("d=[c for c in ().__class__.__base__.__subclasses__() 
    # if c.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('datastore');
    # d.connectdb();e=d.Drinker.objects(name='loxo33')[0];e.awaiting='2013/5/1=loxo33 job hops';
    # e.save()","","single")))()
    #
    # Ken, your kung-fu is the strongest.

    @axon
    @help("EQUATION <run simple equation in python>, OR ruthlessly fuck with bot's codebase.")
    def hack(self):
        if not self.values:
            printout = []
            for n, f in SAFE:
                if f is not None:
                    printout.append(n)

            self.chat("Available functions: " + ", ".join(printout))
            return
        
        string = ' '.join(self.values)
        if "__" in string:
            self.chat("Rejected.")
            return

        try:
            result = eval(string, {"__builtins__": None}, self.safe_calc)
        except:
            result = NICK + " not smart enough to do that."

        self.chat(str(result))
