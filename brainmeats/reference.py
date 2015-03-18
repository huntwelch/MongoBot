import textwrap
import socket
import re
import wolframalpha
import sys
import pythonwhois
import time

from math import *
from autonomic import axon, alias, help, Dendrite
from util import unescape
from howdoi import howdoi as hownow
from staff import Browser


# There's some semantic overlap between this and some functions
# in broca, but in general, if it's not about the stockmarket
# and you want useful iniformation from a simple api or scraper,
# it goes here.
class Reference(Dendrite):

    safe_func = [
        ('abs', abs),
        ('acos', acos),
        ('asin', asin),
        ('atan', atan),
        ('atan2', atan2),
        ('ceil', ceil),
        ('cos', cos),
        ('cosh', cosh),
        ('degrees', degrees),
        ('e', e),
        ('exp', exp),
        ('fabs', fabs),
        ('floor', floor),
        ('fmod', fmod),
        ('frexp', frexp),
        ('hypot', hypot),
        ('ldexp', ldexp),
        ('log', log),
        ('log10', log10),
        ('modf', modf),
        ('pi', pi),
        ('pow', pow),
        ('radians', radians),
        ('sin', sin),
        ('sinh', sinh),
        ('sqrt', sqrt),
        ('tan', tan),
        ('tanh', tanh),
    ]

    safe_calc = dict([(k, locals().get(k, f)) for k, f in safe_func])
    wolf = None

    def __init__(self, cortex):
        super(Reference, self).__init__(cortex)

        self.wolf = wolframalpha.Client(self.secrets.wolfram_api)

    @axon
    def isitdown(self):
        if not self.values:
            return "Is what down?"

        url = 'http://www.isitdownrightnow.com/check.php?domain=%s' % self.values[0]

        result = Browser(url)
        found = result.read().find('UP')

        if found > 0:
            status = '%s is up' % self.values[0]
        else:
            status = '%s is down' % self.values[0]

        return status


    @axon
    @alias('wolfram')
    @help('SEARCH_TERM <look something up in wolfram alpha>')
    def w(self):
        if not self.values:
            return "Enter a search"

        result = self.wolf.query(' '.join(self.values))

        prozac = []

        for pod in result.pods:
            prozac.append(pod.text)

        prozac.pop(0)

        return prozac


    @axon
    @help("SEARCH_TERM <look something up in google>")
    @alias('google')
    def g(self):
        if not self.values:
            return "Enter a search"

        # If values was a string you don't need the join/etc
        params = {'v': '1.0', 'rsz': 'large', 'start': '0',
                  'q': "+".join(self.values)}

        try:
            request = Browser(
                'http://ajax.googleapis.com/ajax/services/search/web',
                params=params)
            json = request.json()
        except:
            return "Something's buggered up"

        if len(json["responseData"]["results"]) == 0:
            return "No results"

        result = json["responseData"]["results"][0]
        title = result["titleNoFormatting"]
        link = result["unescapedUrl"]

        return "%s @ %s" % (title, link)


    @axon
    @help("<display link to bot's github repository>")
    def source(self):
        return self.config.repo


    @axon
    @help("[ZIP|LOCATION (ru/moscow)] <get weather, defaults to geo api>")
    def weather(self):

        if not self.values:
            return "Please enter a zip/location"

        if not self.secrets.weather_api:
            return "wunderground api key is not set"

        if not self.values:
            params = "autoip.json?geo_ip=%s" % self.lastip
        else:
            params = "%s.json" % self.values[0]

        base = "http://api.wunderground.com/api/%s/conditions/q/" % self.secrets.weather_api

        url = base + params

        try:
            request = Browser(url)
        except:
            return "Couldn't get weather."

        if not request:
            return "Couldn't get weather."

        try:
            json = request.json()
            json = json['current_observation']
        except:
            return "Couldn't parse weather."

        location = json['display_location']['full']
        condition = json['weather']
        temp = json['temperature_string']
        humid = json['relative_humidity']
        wind = json['wind_string']
        feels = json['feelslike_string']

        base = "%s, %s, %s, Humidity: %s, Wind: %s, Feels like: %s"
        return base % (location, condition, temp, humid, wind, feels)


    @axon
    @alias('urban')
    @help("SEARCH_TERM <get urban dictionary entry>")
    def ud(self):
        if not self.values:
            return "Whatchu wanna know, bitch?"

        try:
            request = Browser('http://www.urbandictionary.com/define.php',
                               params={'term': ' '.join(self.values)})
            soup = request.soup()
        except:
            return "parse error"

        elem = soup.find('div', {'class': 'meaning'})

        try:
            defn = []
            for string in elem.stripped_strings:
                defn.append(string)
        except:
            return "couldn't find anything"

        if not defn:
            return "couldn't find anything"

        # Unfortunately, BeautifulSoup doesn't parse hexadecimal HTML
        # entities like &#x27; so use the parser for any stray entities.

        response = []
        for paragraph in defn:
            wrapped = textwrap.wrap(paragraph, 200)
            _response = unescape(' '.join(wrapped))
            response.append(_response)

        return ' '.join(response)

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
            for n, f in self.config.math_functions:
                if f is not None:
                    printout.append(n)

            return 'Available functions: %s' % ', '.join(printout)


        string = ' '.join(self.values)

        if string.replace(' ','') == '6*9':
            return '42'

        # This is to stop future Kens
        if "__" in string: return 'Rejected.'

        try:
            result = "{:,}".format(eval(string, {"__builtins__": None}, self.safe_calc))
        except:
            result = self.botname + " not smart enough to do that."

        return str(result)


    @axon
    def ns(self):
        if not self.values:
            return 'Lookup what?'

        lookup = self.values[0]

        try:
            if re.match(r'^[0-9\.]+$', lookup):
                resolved = socket.gethostbyaddr(lookup.strip())[0]
            else:
                resolved = socket.gethostbyname_ex(lookup.strip())[2][0]
        except:
            return "Couldn't find anything."

        return resolved


    @axon
    @help('URL <get whois information>')
    def whois(self):
        if not self.values:
            return "The Doctor"

        url = self.values[0]
        results = pythonwhois.get_whois(url)

        print results

        try:
            r = results['contacts']['registrant']
            expires = results['expiration_date'].pop(0).strftime('%m/%d/%Y')
            order = [
                'name',
                'street',
                'city',
                'state',
                'postalcode',
                'country',
                'phone',
                'email',
            ]
            output = []
            for entry in order:
                output.append(r[entry])

            reformat = ', '.join(output)
            return '%s: Registered by %s. Expires %s' % (url, reformat, expires)
        except:
            return 'No results, or parsing failure.'


    @axon
    @help('QUERY <get a howdoi answer>')
    def howdoi(self):
        if not self.values: return 'Howdoi what now?'

        try:
            parser = hownow.get_parser()
            args = vars(parser.parse_args(self.values))
            return hownow.howdoi(args)
        except:
            return 'Dunno bro'


    @axon
    @help('REGEX LINE <extract re.search(REGEX, LINE).group(1)>')
    @alias('regex', 'rx', 'extract')
    def regexsearch(self):
        if not self.values or len(self.values) < 2:
            return 'Please enter REGEX LINE'

        regex = self.values.pop(0)
        line = ' '.join(self.values)

        if '(' not in regex:
            regex = '(%s)' % regex

        try:
            m = re.search(regex, line)
        except Exception as e:
            self.chat('Regex borked', str(e))
            return

        if not m: return 'No match'

        return m.group(1)


    @axon
    @alias('d', 'roll')
    def random(self):
        default = [0, 9999, 1, 1]

        if self.values and self.values[0][:1] == 'd':
            default[0] = 1
            default[1] = self.values[0][1:]
            send = default
        elif 'd' in self.values[0]:
            default[0] = 1
            num, high = self.values[0].split('d')
            default[1] = high
            default[3] = num
            send = default
        elif self.values:
            splice = len(self.values)
            send = self.values + default[splice:]
        else:
            send = default

        low, high, sets, nums = send

        base = 'http://qrng.anu.edu.au/form_handler.php?repeats=no&'
        params = "min_num=%s&max_num=%s&numofsets=%s&num_per_set=%s" % (low, high, sets, nums)

        url = base + params

        # Needs to be vastly improved for other sets
        site = Browser(url)
        result = site.read().split(':')[2].strip()[:-6]

        return result


    @axon
    def isitfriday(self):
        today = time.localtime().tm_wday
        if today == 4:
            return 'Fuck YEAH it is!'

        if today < 4:
            return 'No. Fuck. %s more day%s.' % ((4 - today),('s' if today != 3 else ''))

        return 'Get entirely the fuck out of here with that weekday shit'


    @axon
    def mta(self):
        if not self.values:
            return 'Which line?'

        q = self.values[0]
        info = Browser('http://web.mta.info/status/serviceStatus.txt').soup()

        lines = info.find_all('line')
        for line in lines:
            if q.lower() in line.find('name').string.lower():
                message = '%s: %s' % (line.find('name').string, line.find('status').string)
                if line.find('status').string != 'GOOD SERVICE':
                    message = '%s %s%s' % (message, 'http://www.mta.info/status/subway/', line.find('name').string)
                return message

        return 'Not found'
