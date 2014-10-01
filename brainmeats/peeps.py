import datetime
import dateutil.parser
import re
import hashlib
import random

from autonomic import axon, help, Dendrite, alias, public, Receptor, Cerebellum
from datastore import simpleupdate, Drinker, incrementEntity, Entity, entityScore, topScores
from server.helpers import totp
from id import Id

# This loosely encapsulates things having to do with
# people in the room. Obviously some overlap with
# other areas, but generally works.
#
# Basically everything here depends on mongodb, and
# many other functions of other libraries refer to peeps
# stuff. If you install no other external stuff, I
# recommend mongodb.
@Cerebellum
class Peeps(Dendrite):

    checked = False
    notifymethods = ['sms', 'email', 'prowl', 'pushover']

    def __init__(self, cortex):
        super(Peeps, self).__init__(cortex)


    @axon
    @help('<show history of the current channel>')
    def history(self):

        try:
            intro = self.cx.channels[self.cx.context].intro
            return [s.strip() for s in intro.splitlines()]
        except:
            return 'Nothing to introduce!'


    @axon
    @help("COMPANY <save your current copmany>")
    def workat(self):
        if not self.values:
            return 'If you\'re unemployed, that\'s cool, just don\'t abuse the bot'

        user = Id(self.lastsender)
        if not user.is_authenticated:
            return 'That\'s cool bro, but I don\'t know you!'

        user.company = ' '.join(self.values)
        return 'I know where you work... watch your back.'


    @axon
    @help("DRINKER <give somebody a point>")
    def increment(self):
        if not self.values:
            self.chat("you need to give someone your love")
            return
        entity = " ".join(self.values)
        if entity == 'jcb':
            return

        if not incrementEntity(entity, random.randint(1, 100000)):
            self.chat("mongodb seems borked")
            return
        return self.lastsender + " brought " + entity + " to " + str(entityScore(entity))


    @axon
    @help("DRINKER <take a point away>")
    def decrement(self):
        if not self.values:
            self.chat("you need to give someone your hate")
            return
        entity = " ".join(self.values)
        if entity == 'jcb':
            return

        if not incrementEntity(entity, random.randint(1, 100000) * -1):
            self.chat("mongodb seems borked")
            return
        return self.lastsender + " brought " + entity + " to " + str(entityScore(entity))


    @axon
    @help("show the leaderboard")
    def leaderboard(self):
        if not self.values:
            limit=5
        else:
            limit = int(self.values[0])

        for drinker in topScores(limit):
            self.chat(drinker.name + " has " + str(drinker.value) + " points")


    @axon
    @help("WHAT <show cumulative score for random thing>")
    def score(self):
        if not self.values: return "For what?"

        s = entityScore(self.values[0])
        if not s: return "Couldn't retrieve score"

        return str(s)


    @axon
    @help("<show where everyone works>")
    def companies(self):
        for drinker in Drinker.objects:
            if "_" not in drinker.name and drinker.company != None:
                self.chat("%s: %s" % (drinker.name, drinker.company))


    @axon
    @help("[USERNAME] <show where you or USERNAME works>")
    def company(self):
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        user = Drinker.objects(name=search_for).first()
        if not user or not user.company:
            self.chat("Tell that deadbeat %s to get a damn job already..." % search_for)
        else:
            self.chat(user.name + ": " + user.company)


    @axon
    @help("<ping everyone in the room>")
    def all(self, whom=False):
        peeps = self.cx.thalamus.channels[self.cx.context]['users']

        announcer = whom or self.lastsender
        announcer = Id(announcer)

        try:
            del peeps[announcer.name]
            del peeps[self.botname]
        except:
            pass

        if not peeps:
            return 'Is this real life? No one to announce anything to...'

        peeps = ', '.join('%s' % (key) for (key, val) in peeps.iteritems())
        return '%s, %s has something very important to say.' % (peeps,
                announcer.name)


    @axon
    @help("YYYY/MM/DD=EVENT_DESCRIPTION <save what you're waiting for>")
    def awaiting(self):
        if not self.values:
            self.chat("Whatchu waitin fo?")
            return

        name = self.lastsender
        awaits = " ".join(self.values)

        drinker = Drinker.objects(name=name)
        if drinker:
            drinker = drinker[0]
            drinker.awaiting = awaits
        else:
            drinker = Drinker(name=name, awaiting=awaiting)

        drinker.save()
        return "Antici..... pating."


    @axon
    @help("[USERNAME] <show what you are or USERNAME is waiting for>")
    def timeleft(self):
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        drinker = Drinker.objects(name=search_for).first()
        if not drinker or not drinker.awaiting:
            self.chat("%s waits for nothing." % search_for)
            return

        try:
            moment, event = drinker.awaiting.split("=")
            year, month, day = moment.split("/")
            delta = datetime.date(int(year), int(month), int(day)) - datetime.date.today()

            return "Only %s days till %s" % (delta.days, event)
        except:
            self.chat("Couldn't parse that out.")


    @axon
    @help("PASSWD <set admin password>")
    def passwd(self):
        whom = Id(self.lastsender)

        if not whom.is_authenticated:
            self.chat('STRANGER DANGER!')
            return

        if not self.values:
            self.chat('Enter a password.')
            return

        if self.context_is_channel:
            self.chat('Not in the channel, you twit.')
            return

        whom.setpassword(' '.join(self.values))
        self.chat('All clear.')


    @axon
    @public
    @help("IDENTIFY <password>")
    def identify(self):
        if not self.values:
            self.chat('Enter a password.')
            return

        if self.context_is_channel:
            self.chat('Not in the channel, you twit.')
            return

        whom = Id(self.lastsender)

        if not whom.identify(' '.join(self.values)):
            self.chat("I don't know you... go away...")
            return

        self.chat('Welcome back %s' % whom.name)


    @axon
    @help("ADDUSER <username>")
    def adduser(self):
        if not self.values:
            self.chat("Who are you trying to add?")
            return

        whom = Id(self.lastsender)

        if not whom.is_authenticated:
            self.chat("I'm sorry, Dave, I'm afraid I can't do that")
            return

        new_user = Id(self.values[0])
        tmp_pass = str(totp.now())
        new_user.setpassword(tmp_pass, True)

        self.chat('Hi %s, your temporary password is %s. Please set up your user '
        'by identifying yourself to me via private message (.identify %s) and '
        'then changing your password (.passwd <newpass>).' % (new_user.nick,
        tmp_pass, tmp_pass), target=new_user.name)


    @axon
    @help("PHONE_NUMBER <add your phone number to your profile for sms access>")
    def addphone(self):
        if not self.values:
            self.chat("What number?")
            return

        phone = self.values[0]

        if not re.search("^[0-9]{10}$", phone):
            self.chat("Just one good ol'merican ten-digit number, thank ya kindly.")
            return

        whom = Id(self.lastsender)
        whom.phone = phone
        self.chat("Number updated.")


    # Placeholder for eventual mutli-platform
    # bot awesomeness
    @axon
    def notifyme(self):
        if not self.values or len(self.values) != 2 or self.values[0] not in notifymethods:
            self.chat('Please enter "sms|email|prowl|pushover and your code/info"')
            return


    @axon
    @help("[USERNAME] <view your own phone number or another drinker's>")
    def digits(self):
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        user = Id(search_for)
        if not user or not user.phone:
            return "No such numba. No such zone."
        else:
            return user.name + ': ' + user.phone


    def meetup(self, hour):

        if hour not in self.checks:
            return

        period, day = self.secrets.meetup.day.split()
        check = dateutil.parser.parse(day)

        if self.checked == check.month:
            return

        self.checks.remove(hour)

        if not self.checks:
            self.checked = check.month

        period = int(period[:1])
        begin = (period - 1) * 7 + 1
        end = period * 7

        if check.day < begin or check.day > end:
            return False

        if datetime.date.today().day != check.day:
            return

        self.all()
        self.announce('Meetup tonight! %s' % self.secrets.meetup.location)


    @axon
    def okdrink(self):
        whenwhere = 'Every %s, %s' % (self.secrets.meetup.day, self.secrets.meetup.location)
        return whenwhere


    # Detect when people are getting incremented, decremented with ++/--
    @Receptor('IRC_PRIVMSG')
    def peep_incdec(self, target, source, args):
        input = args[-1]
        matches = re.match('^([a-zA-Z0-9_\\\[\]\{\}\^`\|]+)([\+|\-]{2}(?![\+|\-])).*', input)

        if not matches:
            return

        entity = matches.group(1)
        method = matches.group(2)

        if not entity:
            return

        source = Id(source)

        if not source.name or not source.is_authenticated:
            return

        mod = 1
        if method == '--':
            mod = -1

        if not incrementEntity(entity, random.randint(1, 100000) * mod):
            self.chat("mongodb seems borked", target=target)
            return

        self.chat('%s brought %s to %d' % (source.name, entity,
            entityScore(entity)), target=target)

