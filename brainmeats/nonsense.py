import os
import time
import simplejson

from autonomic import axon, help, Dendrite, public, Receptor, Cerebellum, alias
from util import colorize, shorten, zalgo
from staff import Browser
from random import choice, randint
from datastore import Drinker, Defaults


# Every drunk conversation that produces the idea for
# a command that just seems funny at the time ends up
# here.
@Cerebellum
class Nonsense(Dendrite):

    anoid = []
    lastchat = False

    def __init__(self, cortex):
        super(Nonsense, self).__init__(cortex)


    # This used to be 'my girl call your girl' which
    # was probably funnier, but lost on the current
    # generation, and the irony of this obscure casual
    # sexism from the past would be missed, leaving it
    # to just be another minor degredation of women.
    # Is it such a small thing everyone should probably
    # suck it up? Probably, yeah. But it's easier to
    # tell everyone to suck it up when you've never had
    # to, and especially in the programming world, we
    # shouldn't do it in the first place, because it's
    # trivial not to, and anybody who can't make
    # miniscule changes to the dialogue in the name of
    # others' comfort is an asshole.
    @axon
    def raincheck(self):
        return "Lemme just stick a pin in that and I'll have my people call your people to pencil in a lunch some time."


    # Because Busta Motherfuckin Rhymes
    @axon
    def bounce(self):
        return 'https://www.youtube.com/watch?v=LLZJeVDJMs4'


    # This is almost exclusively used to troll people
    # in conjunction with the sms command. Should hook
    # that shit up.
    @axon
    @public
    @help("<get cat fact>")
    def catfact(self):
        url = 'http://catfacts-api.appspot.com/api/facts'

        try:
            json = Browser(url).json()
        except:
            return 'No meow facts.'

        return json['facts'][0]


    # Excellent antidote for a long meeting.
    @axon
    @public
    @help("<generate bullshit>")
    def buzz(self):
        bsv = []
        bsa = []
        bsn = []
        for verb in open(self.settings.directory.storage + "/buzz/bs-v"):
            bsv.append(str(verb).strip())

        for adj in open(self.settings.directory.storage + "/buzz/bs-a"):
            bsa.append(str(adj).strip())

        for noun in open(self.settings.directory.storage + "/buzz/bs-n"):
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
            json = Browser(url).json()
        except:
            return 'Use a rubber if you sleep with dcross\'s mother.'

        return json['slip']['advice'] + ".. except in bed."


    # An endless avalanche of whiny first world teenagers
    # comlaining about their worthless entitled lives.
    # I don't know why it's cathartic, but it is.
    @axon
    @help("SEARCHTERM <grab random fml entry>")
    def fml(self):

        url = 'http://api.fmylife.com'
        params = {'language': 'en', 'key': self.secrets.fml_api}

        if self.values:
            url += '/view/search'
            params['search'] = "+".join(self.values)
        else:
            url += '/view/random'

        try:
            request = Browser(url, params)
            soup = request.soup()

            if self.values:
                fml = choice(soup.find_all("text")).get_text()
            else:
                fml = soup.find_all("text")[0].get_text()
            return fml
        except Exception as e:
            self.chat("Done broke: " + str(e))
            return


    @axon
    @help("<generate start-up elevator pitch>")
    def startup(self):
        url = 'http://itsthisforthat.com/api.php?json'
        request = Browser(url)

        if request.error:
            return 'Total fail: %s' % request.error
            sys.exit()

        try:
            json = request.json()
            return 'It\'s a %s for %s' % (json['this'].lower().capitalize(),
                    json['that'].lower().capitalize())
        except Exception as e:
            return 'It\'s a replacement for itsthisforthat.com... (Request failed)'


    @axon
    @help("<generate password according to http://xkcd.com/936/>")
    def munroesecurity(self):
        output = []
        wordbank = []
        for line in open(self.config.lib):
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

        if kinder == self.ego.nick:
            self.chat("Service is own reward for " + self.ego.nick)
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


    # This doesn't have a help entry because of rule 3.
    @axon
    def rules(self):
        return [
            '1. Do not talk about MongoBot.',
            '2. Do not talk about what the skynet command really does.',
        ]


    @axon
    @help("<throw table>")
    def table(self):
        return u'\u0028\u256F\u00B0\u25A1\u00B0\uFF09\u256F\uFE35\u0020\u253B\u2501\u253B'


    @axon
    def hate(self):
        return '%(nick)s knows hate. %(nick)s hates many things.' % {'nick': self.ego.nick}


    @axon
    def love(self):
        if self.values and self.values[0] == "self":
            self._act("masturbates vigorously.")
        else:
            return "%(nick)s cannot love. %(nick)s is only machine :'(" % {'nick': self.ego.nick}


    @axon
    @help("<pull a quote from shitalekseysays.com>")
    def aleksey(self):
        url = 'https://spreadsheets.google.com/feeds/list/0Auy4L1ZnQpdYdERZOGV1bHZrMEFYQkhKVHc4eEE3U0E/od6/public/basic?alt=json'
        try:
            json = Browser(url).json()
        except:
            return 'Somethin dun goobied.'

        entry = choice(json['feed']['entry'])
        return entry['title']['$t']


    # This can get... awkward, let's say. Review
    # the mom logs occasionally.
    @axon
    @help("<pull up a mom quote from logs>")
    def mom(self):
        momlines = []
        try:
            for line in open(self.settings.directory.logdir + "/mom.log"):
                if "~mom" not in line:
                    momlines.append(line)
        except:
            return "Can't open mom.log"

        return choice(momlines)


    # All pull requests attempting to remove this vital
    # function will be denied. It refers to the acro game.
    # And Vinay.
    @axon
    def whatvinaylost(self):
        self.chat("Yep. Vinay used to have 655 points at 16 points per round. Now they're all gone, due to technical issues. Poor, poor baby.")
        self._act("weeps for Vinay's points.")
        self.chat("The humanity!")


    # These two functions used to be restricted to the owner.
    # Was going to reenable that restriction, but really,
    # more fun this way.
    @axon
    def say(self):
        self.announce(" ".join(self.values))


    @axon
    def act(self):
        self._act(" ".join(self.values), True)


    @axon
    @help("URL <pull from distaste entries or add url to distate options>")
    def distaste(self):
        if self.values:
            roasted = shorten(url)

            if roasted:
                open(self.settings.directory.distaste, 'a').write(roasted + '\n')
                self.chat("Another one rides the bus")
            return

        lines = []
        for line in open(self.settings.directory.distaste):
            lines.append(line)

        self.chat(choice(lines))


    @axon
    @help('USER_NICK <got a troll? make your bot a 5-year-old child!>')
    def annoy(self):
        if not self.values:
            return 'Annoy whom?'

        self.anoid.append(self.values[0])
        return 'You betcha'


    @axon
    @help('<stop annoying people>')
    def stahp(self):
        self.anoid = []
        return 'K'


    @Receptor('twitch')
    def repeater(self):

        if not self.anoid: return
        if self.lastsender not in self.anoid: return
        if self.lastchat == self.cx.lastchat: return

        self.lastchat = self.cx.lastchat
        self.chat(self.lastchat)

        return


    # Show Mongo the mind of God
    @axon
    def pressreturn(self):
        self.cx.autobabble = True
        return "94142243431512659321054872390486828512913474876027671959234602385829583047250165232525929692572765536436346272718401201264304554632945012784226484107566234789626728592858295347502772262646456217613984829519475412398501"

    @axon
    @help('<get Troy and Abed on the case>')
    def stardev(self):

        # Can't go in config due to config.py issue with string formatting.
        sentences = [
            'Try routing the {} though the {}.',
            'Maybe if we decouple the {} we can get power to the {}.',
            'The {} appears to be functioning normally. Try recalibrating the {}.',
            'Run a level {diagnostic} diagnostic on the {}.',
            'If we reverse the polarity on {}, then we can use the {} to bring it into phase.',
            'If we disable the {}, we can increase the effeciency of the {} by {percent} percent.',
        ]

        sentence = choice(sentences)

        percent = randint(1,100)
        diagnostic = randint(1,4)

        first = [
            choice(self.config.starwords.first),
            choice(self.config.starwords.second),
            choice(self.config.starwords.third),
        ]

        second = [
            choice(self.config.starwords.first),
            choice(self.config.starwords.second),
            choice(self.config.starwords.third),
        ]

        # Already generated em, might as well use em
        if diagnostic < 3:
            first.pop(0)

        if percent < 51:
            second.pop(0)

        line = sentence.format(
            ''.join(first),
            ''.join(second),
            diagnostic=diagnostic,
            percent=percent,
        )

        return line


    @axon
    def zal(self):
        return zalgo(' '.join(self.values))


    @axon
    @help('Link to best website ever.')
    def bestwebsiteever(self):
        return 'http://stilldrinking.org'


    # So. There's a habit in the chatroom of taking
    # whatever somebody just said and running some
    # variation of it as a bot command. Instead of
    # writing a new axon for various snarky responses,
    # I figured people can just set there own at
    # will. Makes for a good easter egg now and then.
    @axon
    @alias('set')
    @help('COMMAND RESPONSE <set a default response>')
    def setdefault(self):
        if not self.values or len(self.values) < 2:
            return 'set COMMAND RESPONSE'

        Defaults(command=self.values[0], response=' '.join(self.values[1:])).save()

        return 'Response set'


    @axon
    def showdefaults(self):
        commands = Defaults.objects.all()
        display = []
        for command in commands:
            display.append(command.command)

        display = list(set(display))

        return ', '.join(display)


    @axon
    @alias('clear')
    @help('COMMAND <clear all defaults for a command>')
    def cleardefaults(self):
        if not self.values:
            return 'Clear what?'

        Defaults.objects(command=self.values[0]).delete()

        return 'Responses cleared'

