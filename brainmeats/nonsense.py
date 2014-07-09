import os
import time

from autonomic import axon, help, Dendrite
from settings import STORAGE, ACROLIB, LOGDIR, DISTASTE, NICK, IMGS
from secrets import FML_API
from util import colorize, pageopen, shorten, asciiart
from random import choice
from datastore import Drinker
from xml.dom import minidom as dom


# Every drunk conversation that produces the idea for
# a command that just seems funny at the time ends up
# here.
class Nonsense(Dendrite):

    anoid = []
    lastchat = False

    def __init__(self, cortex):
        super(Nonsense, self).__init__(cortex)

    @axon
    @help("<generate bullshit>")
    def buzz(self):
        bsv = []
        bsa = []
        bsn = []
        for verb in open(STORAGE + "/buzz/bs-v"):
            bsv.append(str(verb).strip())

        for adj in open(STORAGE + "/buzz/bs-a"):
            bsa.append(str(adj).strip())

        for noun in open(STORAGE + "/buzz/bs-n"):
            bsn.append(str(noun).strip())

        buzzed = [
            choice(bsv),
            choice(bsa),
            choice(bsn),
        ]

        return ' '.join(buzzed)

    @axon
    @help("<grab a little advice>")
    def advice(self):
        url = 'http://api.adviceslip.com/advice'

        try:
            json = pageopen(url).json()
        except:
            return 'Use a rubber if you sleep with dcross2\'s mother.'

        return json['slip']['advice'] + ".. in bed."

    @axon
    @help("SEARCHTERM <grab random fml entry>")
    def fml(self):

        url = 'http://api.fmylife.com'
        params = {'language': 'en', 'key': FML_API}

        if self.values and self.values[0]:
            url += '/view/search'
            params['search'] = "+".join(self.values)
        else:
            url += '/view/random'

        try:
            response = pageopen(url, params)
            raw = dom.parseString(response.text)
            if self.values and self.values[0]:
                fml = choice(raw.getElementsByTagName("text")).firstChild.nodeValue
            else:
                fml = raw.getElementsByTagName("text")[0].firstChild.nodeValue
            return fml
        except Exception as e:
            if self.values and self.values[0]:
                self.chat("No results. Or done broken.")
            else:
                self.chat("Done broke")
                self.chat("Exception: " + str(e))
            return

    @axon
    @help("<generate start-up elevator pitch>")
    def startup(self):
        url = 'http://itsthisforthat.com/api.php?text'

        try:
            out = pageopen(url).text
            return out.lower().capitalize()
        except:
            self.chat("Done broke")
            return

    @axon
    @help("<generate password according to http://xkcd.com/936/>")
    def munroesecurity(self):
        output = []
        wordbank = []
        for line in open(STORAGE + "/" + ACROLIB):
            wordbank.append(line.strip())

        count = 0
        while count < 4:
            word = choice(wordbank).lower()
            output.append(word)
            count += 1

        return " ".join(output)

    @axon
    @help("USERNAME <reward someone>")
    def reward(self):
        if not self.values:
            self.chat("Reward whom?")
            return
        kinder = self.values[0]

        if kinder == NICK:
            self.chat("Service is own reward for " + NICK)
            return

        drinker = Drinker.objects(name=kinder)
        if drinker:
            drinker = drinker[0]
            rewards = drinker.rewards + 1
        else:
            drinker = Drinker(name=kinder)
            rewards = 1

        drinker.rewards = rewards
        drinker.save()

        self.chat("Good job, " + kinder + ". Here's your star: " + colorize(u'\u2605', "yellow"))
        self._act(" pats " + kinder + "'s head.")

    @axon
    def cry(self):
        self._act("cries.")

    @axon
    def skynet(self):
        return 'Activating.'

    @axon
    @help("<throw table>")
    def table(self):
        return u'\u0028\u256F\u00B0\u25A1\u00B0\uFF09\u256F\uFE35\u0020\u253B\u2501\u253B'

    @axon
    def hate(self):
        return '%(nick)s knows hate. %(nick)s hates many things.' % {'nick': NICK}

    @axon
    def love(self):
        if self.values and self.values[0] == "self":
            self._act("masturbates vigorously.")
        else:
            return "%(nick)s cannot love. %(nick)s is only machine :'(" % {'nick': NICK}

    @axon
    @help("<pull a quote from shitalekseysays.com>")
    def aleksey(self):
        url = 'https://spreadsheets.google.com/feeds/list/0Auy4L1ZnQpdYdERZOGV1bHZrMEFYQkhKVHc4eEE3U0E/od6/public/basic?alt=json'
        try:
            response = pageopen(url)
            json = response.json()
        except:
            return 'Somethin dun goobied.'

        entry = choice(json['feed']['entry'])
        return entry['title']['$t']

    @axon
    @help("<pull up a mom quote from logs>")
    def mom(self):
        momlines = []
        try:
            for line in open(LOGDIR + "/mom.log"):
                if "~mom" not in line:
                    momlines.append(line)
        except:
            return "Can't open mom.log"

        return choice(momlines)

    @axon
    def whatvinaylost(self):
        self.chat("Yep. Vinay used to have 655 points at 16 points per round. Now they're all gone, due to technical issues. Poor, poor baby.")
        self._act("weeps for Vinay's points.")
        self.chat("The humanity!")

    @axon
    def say(self):
        if self.validate():
            self.announce(" ".join(self.values))

    @axon
    def act(self):
        if self.validate():
            self._act(" ".join(self.values), True)

    @axon
    @help("URL <pull from distaste entries or add url to distate options>")
    def distaste(self):
        if self.values:
            roasted = shorten(url)

            if roasted:
                open(DISTASTE, 'a').write(roasted + '\n')
                self.chat("Another one rides the bus")
            return

        lines = []
        for line in open(DISTASTE):
            lines.append(line)

        self.chat(choice(lines))

    @axon
    def annoy(self):
        if not self.values:
            return 'Annoy whom?'

        self.anoid.append(self.values[0])
        self.cx.addlive(self.repeater)
        return 'You betcha'

    @axon
    def stahp(self):
        self.cx.droplive('repeater')
        self.anoid = []
        return 'K'

    def repeater(self):
        if self.lastsender in self.anoid:
            if self.lastchat == self.cx.lastchat:
                return

            self.lastchat = self.cx.lastchat
            self.chat(self.lastchat)
            return

    # Show Mongo the mind of God
    @axon
    def pressreturn(self):
        self.cx.autobabble = True
        return "94142243431512659321054872390486828512913474876027671959234602385829583047250165232525929692572765536436346272718401201264304554632945012784226484107566234789626728592858295347502772262646456217613984829519475412398501"
