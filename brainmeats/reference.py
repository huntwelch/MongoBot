import textwrap
import socket
import re

from autonomic import axon, alias, help, Dendrite
from bs4 import BeautifulSoup as bs4
from settings import REPO, NICK, SAFE
from secrets import WEATHER_API
from util import unescape, pageopen
from howdoi import howdoi as hownow


# There's some semantic overlap between this and some functions
# in broca, but in general, if it's not about the stockmarket
# and you want useful iniformation from a simple api or scraper,
# it goes here.
class Reference(Dendrite):

    safe_calc = dict([(k, locals().get(k, f)) for k, f in SAFE])

    def __init__(self, cortex):
        super(Reference, self).__init__(cortex)

    @axon
    @help("SEARCH_TERM <look something up in google>")
    def g(self):
        if not self.values:
            self.chat("Enter a word")
            return

        # If values was a string you don't need the join/etc
        params = {'v': '1.0', 'rsz': 'large', 'start': '0',
                  'q': "+".join(self.values)}

        try:
            request = pageopen(
                'http://ajax.googleapis.com/ajax/services/search/web',
                params=params)
            json = request.json()
        except:
            self.chat("Something's buggered up")
            return

        if len(json["responseData"]["results"]) == 0:
            self.chat("No results")
            return

        result = json["responseData"]["results"][0]
        title = result["titleNoFormatting"]
        link = result["unescapedUrl"]

        return "%s @ %s" % (title, link)

    @axon
    @help("<display link to bot's github repository>")
    def source(self):
        return REPO

    @axon
    @help("[ZIP|LOCATION (ru/moscow)] <get weather, defaults to geo api>")
    def weather(self):
        if not WEATHER_API:
            self.chat("WEATHER_API is not set")
            return

        if not self.values:
            params = "autoip.json?geo_ip=%s" % self.lastip
        else:
            params = "%s.json" % self.values[0]

        base = "http://api.wunderground.com/api/%s/conditions/q/" % WEATHER_API

        url = base + params

        try:
            response = pageopen(url)
        except:
            self.chat("Couldn't get weather.")
            return

        if not response:
            self.chat("Couldn't get weather.")
            return

        try:
            json = response.json()
            json = json['current_observation']
        except:
            self.chat("Couldn't parse weather.")
            return

        location = json['display_location']['full']
        condition = json['weather']
        temp = json['temperature_string']
        humid = json['relative_humidity']
        wind = json['wind_string']
        feels = json['feelslike_string']

        base = "%s, %s, %s, Humidity: %s, Wind: %s, Feels like: %s"
        return base % (location, condition, temp, humid, wind, feels)

    @axon
    @alias(["urban"])
    @help("SEARCH_TERM <get urban dictionary entry>")
    def ud(self):
        if not self.values:
            self.chat("Whatchu wanna know, bitch?")
            return

        try:
            request = pageopen('http://www.urbandictionary.com/define.php',
                               params={'term': ' '.join(self.values)})
            soup = bs4(request.text)
        except:
            self.chat("parse error")
            return

        elem = soup.find('div', {'class': 'meaning'})

        try:
            defn = []
            for string in elem.stripped_strings:
                defn.append(string)
        except:
            self.chat("couldn't find anything")


        if defn:
            # Unfortunately, BeautifulSoup doesn't parse hexadecimal HTML
            # entities like &#x27; so use the parser for any stray entities.
            for paragraph in defn:
                wrapped = textwrap.wrap(paragraph, 200)
                for line in wrapped:
                    self.chat(unescape(line))
        else:
            self.chat("couldn't find anything")

    # This function used to be called calc, but was changed to hack in
    # honor of Ken's incredibly sick exploitation of the eval function,
    # which gave him direct access to the database:
    #
    # (lambda f=(lambda n:[c for c in ().__class__.__bases__[0].__subclasses__()
    # if c.__name__=='catch_warnings'][0]()._module.__builtins__[n]):
    # f("eval")(f("compile")("d=[c for c in ().__class__.__base__.__subclasses__()
    # if c.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('datastore');
    # d.connectdb();e=d.Drinker.objects(name='redacted')[0];e.awaiting='2013/5/1=redacted job hops';
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

        # This is to stop future Kens
        if "__" in string:
            self.chat("Rejected.")
            return

        try:
            result = "{:,}".format(eval(string, {"__builtins__": None}, self.safe_calc))
        except:
            result = NICK + " not smart enough to do that."

        return str(result)

    @axon
    def ns(self):
        if not self.values:
            self.chat("Lookup what?")
            return

        lookup = self.values[0]

        try:
            if re.match(r'^[0-9\.]+$', lookup):
                resolved = socket.gethostbyaddr(lookup.strip())[0]
            else:
                resolved = socket.gethostbyname_ex(lookup.strip())[2][0]
        except:
            self.chat("Couldn't find anything.")
            return
        
        return resolved

    # I wanted to do a good whois function, but whois parsing is
    # a shitshow even stackoverflow balked at. If you know of or
    # want to create a solid parser for it, go for it. I'll take
    # that pull request like a crack whore.
    @axon
    @help('URL <get whois information>')
    def whois(self):
        return "The Doctor"

    @axon
    @help('QUERY <get a howdoi answer>')
    def howdoi(self):
        if not self.values:
            return 'Howdoi what now?'

        try:
            parser = hownow.get_parser()
            args = vars(parser.parse_args(self.values))
            return hownow.howdoi(args) 
        except:
            return 'Dunno bro'

    # TODO: save common regexs
    @axon
    @help('REGEX LINE <extract re.search(REGEX, LINE).group(1)>')
    @alias(['regex', 'rx', 'extract'])
    def regexsearch(self):
        if not self.values or len(self.values) < 2:
            self.chat('Please enter REGEX LINE')
            return

        regex = self.values.pop(0)
        line = ' '.join(self.values)

        m = re.search(regex, line)

        if not m:
            self.chat('No match')
            return

        return m.group(1)
