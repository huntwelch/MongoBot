import MySQLdb
import simplejson
import urllib
import urllib2
import random 

from autonomic import axon, category, help, Dendrite
from settings import STORAGE, ACROLIB, LOGDIR, SHORTENER, DISTASTE, SQL_PASSWORD
from util import colorize


@category("nonsense")
class Nonsense(Dendrite):
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
            random.choice(bsv),
            random.choice(bsa),
            random.choice(bsn),
        ]

        self.chat(' '.join(buzzed))

    # TODO: Stick data in mongodb
    @axon
    @help("<grab random fml entry>")
    def fml(self):
        db = MySQLdb.connect("localhost","peter",SQL_PASSWORD,"peter_stilldrinking") 
        cursor = db.cursor()
        cursor.execute("SELECT * FROM fmls ORDER BY RAND() LIMIT 0,1;")
        entry = cursor.fetchone()
        fml = entry[2]
        self.chat(fml)

    @axon
    @help("<generate passward according to http://xkcd.com/936/>")
    def munroesecurity(self):
        output = []
        wordbank = []
        for line in open(STORAGE + "/" + ACROLIB):
            wordbank.append(line.strip())

        count = 0
        while count < 4:
            word = random.choice(wordbank).lower()
            output.append(word)
            count += 1

        self.chat(" ".join(output))

    @axon
    @help("[user] <reward someone>")
    def reward(self):
        self.snag()
        if not self.values:
            self.chat("Reward whom?")
            return
        kinder = self.values[0]
        self.chat("Good job, " + kinder + ". Here's your star: " + colorize(u'\u2605',"yellow"))
        self.act(" pats " + kinder + "'s head.")
        
    @axon
    def cry(self):
        self.act("cries.")

    @axon
    def skynet(self):
        self.chat("Activating.")

    @axon
    @help("<throw table>")
    def table(self):
        self.chat(u'\u0028' + u'\u256F' + u'\u00B0' + u'\u25A1' + u'\u00B0' + u'\uFF09' + u'\u256F' + u'\uFE35' + u'\u0020' + u'\u253B' + u'\u2501' + u'\u253B')

    @axon
    def hate(self):
        self.chat(NICK + " knows hate. " + NICK + " hates many things.")

    @axon
    def love(self):
        self.snag()
        if self.values and self.values[0] == "self":
            self.act("masturbates vigorously.")
        else:
            self.chat(NICK + " cannot love. " + NICK + " is only machine :'(")

    @axon
    @help("<pull a quote from shitalekseysays.com>")
    def aleksey(self):
        url = 'https://spreadsheets.google.com/feeds/list/0Auy4L1ZnQpdYdERZOGV1bHZrMEFYQkhKVHc4eEE3U0E/od6/public/basic?alt=json'
        try:
            response = urllib2.urlopen(url).read()
            json = simplejson.loads(response)
        except:
            self.chat('Somethin dun goobied.')
            return

        entry = choice(json['feed']['entry'])
        self.chat(entry['title']['$t'])

    @axon
    @help("<pull up a mom quote>")
    def mom(self):
        momlines = []
        for line in open(LOGDIR + "/mom.log"):
            momlines.append(line)

        self.chat(random.choice(momlines))

    @axon
    def whatvinaylost(self):
        self.chat("Yep. Vinay used to have 655 points at 16 points per round. Now they're all gone, due to technical issues. Poor, poor baby.")
        self.act("weeps for Vinay's points.")
        self.chat("The humanity!")

    @axon
    def say(self):
        self.snag()
        if self.validate():
            self.announce(" ".join(self.values))

    @axon
    def act(self):
        self.snag()
        if self.validate():
            self._act(" ".join(self.values), True)

    @axon
    def distaste(self):
        self.snag()
        if self.values:
            url = urllib.quote_plus(self.values[0])
            roasted = urllib2.urlopen(SHORTENER + url).read()

            open(DISTASTE, 'a').write(roasted + '\n')
            self.chat("Another one rides the bus")
            return

        lines = []
        for line in open(DISTASTE):
            lines.append(line)

        self.chat(random.choice(lines))

