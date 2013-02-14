import simplejson
import urllib
import re

from autonomic import axon, category, help, Dendrite
from settings import REPO, NICK, SAFE
from secrets import WEATHER_API
from util import pageopen


@category("reference")
class Reference(Dendrite):
    def __init__(self, cortex):
        super(Reference, self).__init__(cortex)

        self.safe_calc = dict([(k, locals().get(k, f)) for k, f in SAFE])

    @axon
    @help("search_term <look something up in google>")
    def g(self):
        self.snag()

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
    @help("zip_code <get weather>")
    def weather(self):
        self.snag()

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

    # TODO: This is totally broken for some reason
    @axon
    @help("equation <run simple equation in python>")
    def calc(self):
        self.snag()

        if not self.values:
            printout = []
            for n, f in SAFE:
                if f is not None:
                    printout.append(n)

            self.chat("Available functions: " + ", ".join(printout))
            return
        try:
            result = eval(' '.join(self.values), {"__builtins__": None}, self.safe_calc)
        except:
            result = NICK + " not smart enough to do that."

        self.chat(str(result))
