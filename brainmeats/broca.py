import re
import string
import random
import redis
import time
import os

from autonomic import axon, alias, help, Dendrite, public, Receptor, Cerebellum

from datastore import Words, Learned, Structure
from random import choice, randint
from util import savefromweb
from staff import Browser
from wordnik import swagger, WordApi
from id import Id


# The miscellaneous language functions
# usually work, and of course the markov
# is done here.
@Cerebellum
class Broca(Dendrite):

    readstuff = False
    knowledge = False
    draft = False

    def __init__(self, cortex):
        super(Broca, self).__init__(cortex)
        self.markov = redis.StrictRedis(unix_socket_path=self.cx.settings.sys.redissock)


    # This can get stuck sometimes. Seems to be working
    # better these days, but a .reload should handle it.
    # All these compose functions could use a little
    # cleaning up.
    @axon
    @help('TITLE <compose poetry>')
    def compose(self):
        if not self.startpoem(): return

        poem = ''
        seed = self.babble()

        if not seed:
            return 'Muse not with %s today' % self.ego.nick

        seed = seed.split()
        for word in seed:
            mas = self.babble([word])
            if not mas: continue

            poem = '%s %s' % (poem, mas)

        self.addtext(poem.split())
        res = self.finis()

        return res


    @axon
    @alias('begin')
    def startpoem(self):

        title = 'Untitled'
        if self.values:
            title = ' '.join(self.values)

        if self.draft:
            self.chat('Little busy right now')
            return False

        filename = '%s.txt' % re.sub('[^0-9a-zA-Z]+', '_', title)

        if os.path.isfile('%s/%s' % (self.cx.settings.media.poems, filename)):
            self.chat('Already wrote that')
            return False

        draft = open('%s/%s' % (self.cx.settings.media.poems, filename), 'a')
        draft.write('%s\n' % title)
        draft.close()

        self.draft = filename

        self.chat('%s think "%s" may be masterpiece' % (self.ego.nick, title))
        return True


    @axon
    @alias('write', 'explicit')
    def addtext(self, what=False):

        # TODO: calling with .explicit will disable random line breaks

        if not self.draft:
            return 'No poems open now.'

        draft = open('%s/%s' % (self.cx.settings.media.poems, self.draft), 'a')

        what = what or self.values

        text = ''
        while what:
            if random.randint(0,10) == 5:
                addition = '\n'
            else:
                addition = what.pop(0)

            text = '%s %s' % (text, addition)

        draft.write(text)
        draft.close()

        return 'Coming along real good'


    @axon
    def finis(self):
        link = '%s/poem/%s' % (self.cx.settings.website.url, self.draft[:-4])
        self.draft = False
        return 'Work complete: %s' % link


    @axon
    def mark(self, line):
        words = line.split()

        while len(words) > 2:
            word = words.pop(0)
            prefix = "%s %s" % (word, words[0])
            follow = words[1]

            entry = self.markov.get(prefix)
            if not entry:
                self.markov.set(prefix, follow)
            else:
                follows = entry.split(',')
                follows.append(follow)
                follow = ','.join(follows)
                self.markov.set(prefix, follow)


    @axon
    @help('URL_OF_TEXT_FILE <Read something>')
    def read(self):
        if not self.values:
            return "Read what?"


        book = self.values[0]
        if book[-4:] != '.txt':
            return "Plain text file only. %s purist." % self.ego.nick


        name = "%s_%s.txt" % ( int(time.mktime(time.localtime())), self.lastsender )
        path = '%s/%s' % (self.cx.settings.media.books, name)

        savefromweb(book, path)
        with open(path) as b:
            for line in b:
                self.mark(line)

        return 'Eh, I like his older, funnier work'


    # MongoBot's ability to run a markov chain is a large
    # part of the reason I started working on mongo in the
    # first place.
    #
    # (cough)
    #
    # So MongoBot was made on a whim in the chatroom of his
    # birth just because I wanted to know how to make a bot.
    # Since at the time I was pretty checked out of my job
    # I put an awful lot of work into him, and he eventually
    # edged out ExStaffRobot as the dominant bot.
    #
    # ExStaffRobot itself was a descendent of StaffRobot,
    # the dev irc chatbot that warned us about failures and
    # stuff at OkCupid (the Staff Robot that pops up all
    # over OkCupid is itself a rendering of this StaffRobot
    # by one of the frontend designers. He and I never got
    # on, but he does draw a mean bot). This StaffRobot had
    # a markov chat function in it, which I didn't really
    # understand at the time, as I was scared of all these
    # awesome CS majors, and was, essentially, an out-of-work
    # film student who only got the job because a few of the
    # powers that were didn't think frontend programmers
    # needed to be very smart. But I really wanted to put a
    # markov chain in my bot, partly to understand and because
    # I missed the old bot after one of the founders bitched
    # about it being annoying until we had to turn it off,
    # and another small piece of the personality that kept me
    # at the job through the first year of death camp hours
    # was wicked away.
    #
    # So three years after MongoBot made his first appearance
    # I finally faced my fears of inferiority and looked up
    # a markov chain on wikipedia, where I discovered it was,
    # in fact, totally fucking trivial.
    #
    # It reminds me a bit of a video editor who was training
    # me on an internship, and I asked him how to do split
    # screen and he said he didn't think I was ready for that
    # yet, so I just taught myself. When he found out, he
    # got so upset he walked out of the room. Point is,
    # Americans have some seriously fucked up problems with
    # their opinions on the nature and value of intelligence.
    @axon
    @public
    @alias('waxrhapsodic')
    @help('<Speak markov chain>')
    def babble(self, what=False):

        suppress = False
        if what:
            suppress = True

        what = what or self.values

        if what:
            if len(what) > 1:
                pattern = "%s %s" % (what[0], what[1])
            else:
                pattern = "*%s*" % what[0]

            matches = self.markov.keys(pattern)

            if not matches and not suppress:
                return 'Got nothin'

            seed = random.choice(matches)
        else:
            seed = self.markov.randomkey()

        words = seed.split()

        follows = self.markov.get(seed)
        follows = follows.split(',')
        words.append(random.choice(follows))

        suspense = [
            'and', 'to', 'a', 'but', 'very',
            'the', 'when', 'how', '', ' ', 'my',
            'its', 'of', 'is', 'for', 'the',
        ]

        while len(words) < self.config.babblelim:
            tail = "%s %s" % (words[-2], words[-1])
            follows = self.markov.get(tail)
            if not follows:
                if words[-1].lower().strip() in suspense:
                    seed = self.markov.randomkey()
                    follows = self.markov.get(seed)
                else:
                    break
            follows = follows.split(',')
            words.append(random.choice(follows))

        words = ' '.join(words)
        rep = re.compile('[\()\[\]"]')
        words = rep.sub('', words)
        words = words.split()

        # Mostly, security in babble is your
        # problem, but botpass shows up in the
        # channel a lot.
        while self.cx.secrets.system.botpass in words:
            words.remove(self.cx.secrets.system.botpass)

        words = ' '.join(words)

        # Tweet this
        # First make sure it's short enough
        # only tweet 20% of babble
        if len(words) <= 140 and random.randrange(1,5) == 1:
            tweet_data = []
            for word in words.split(' '):
                if len(word) >= 4 and random.randrange(1, 4) == 1:
                    if random.randrange(1, 3) == 1:
                        word = '#' + word
                    else:
                        word = '@' + word
                tweet_data.append(word)
            self.cx.commands.get('tweet')(" ".join(tweet_data))

        return words

    # TODO: clean up relationship between whatmean/wordnik/seekdef
    @axon
    @alias('d')
    @help('WORD <get definition of word>')
    def whatmean(self):
        if not self.values:
            return "Ooohhhmmmmm"

        word = self.values[0]
        which = 0

        self.definitions = Words.objects(word=word)

        if len(self.values) == 2:
            try:
                which = int(self.values[1]) - 1
            except:
                self.chat("Invalid index. Defaulting to 1.")

        try:
            definition = self.definitions[which]["definition"]
        except:
            self.chat("Can't find a definition. Pinging wordnik...")
            try:
                self.seekdef(word)
            except Exception as e:
                self.chat("Wordnik broke.", error=str(e))
            return

        self.chat("%s definitions for %s" % (str(len(self.definitions)), word))

        return "Definition %s: %s" % (str(which + 1), definition)

    def seekdef(self, word):
        if not self.secrets.wordnik_api:
            return "No api key is not set."

        client = swagger.ApiClient(self.secrets.wordnik_api, 'http://api.wordnik.com/v4')
        wapi = WordApi.WordApi(client)
        results = wapi.getDefinitions(word.strip())

        count = 0

        if not results:
            self.chat('I got nothin.')
            return

        for item in results:

            try:
                definition = Words(word=item.word,
                                   partofspeech=item.partOfSpeech,
                                   definition=item.text,
                                   source=item.sourceDictionary)

                definition.save()
                if count == 0:
                    tempdef = item.text

                count += 1
            except Exception as e:
                print e
                continue

        if count > 0:
            self.chat("Wordnik coughed up " + str(count) + " definitions.")
            self.chat("Definition 1:" + tempdef)
        else:
            return "I got nothin."


    # This is where all the conversational tics and
    # automatic reactions are set up. Also, for some
    # reason, the mom log, because it's awesome but
    # maybe not cortex material. Is the name of this
    # function in poor taste? Yes.
    @Receptor('IRC_PRIVMSG')
    def tourettes(self, target, source, args):
        sentence = args[-1]
        whom = Id(source)
        nick = whom.nick

        if "mom" in sentence.translate(string.maketrans("", ""), string.punctuation).split():
            open("%s/mom.log" % self.cx.settings.directory.logdir, 'a').write(sentence + '\n')

        # This could be more like a dict
        if sentence.lower().find("oh snap") != -1:
            self.chat("yeah WHAT?? Oh yes he DID", target=target)
            return

        if sentence.lower() == 'boom':
            self.chat(u'(\u2022_\u2022)', target=target)
            self.chat(u'( \u2022_\u2022)>\u2310 \u25A1-\u25A1', target=target)
            self.chat(u'(\u2310 \u25A1_\u25A1)', target=target)
            return

        if sentence.lower() == "sup":
            self.chat("chillin", target=target)
            return

        if sentence.lower().find("murica") != -1:
            self.chat("fuck yeah", target=target)
            return

        if sentence.lower().find("hail satan") != -1:
            self.chat(u"\u26E7\u26E7\u26E7\u26E7\u26E7", target=target)
            return

        if sentence.lower().find("race condition") != -1:
            self.chat("It's never a race condition.", target=target)
            return

        if sentence.lower().find("rimshot") != -1:
            self.chat("*ting*", target=target)
            return

        if sentence.lower().find("stop") == len(sentence) - 4 and len(sentence) != 3:
            stops = [
                'Hammertime',
                "Children, what's that sound",
                'Collaborate and listen',
            ]
            self.chat(random.choice(stops), target=target)
            return

        if sentence.lower().find("idk") != -1:
            self.chat(u'\u00AF\u005C\u005F\u0028\u30C4\u0029\u005F\u002F\u00AF', target=target)
            return

        if sentence.lower().strip() in self.config.frustration or sentence.lower().find('stupid') == 0:
            self.chat(self.cx.commands.get('table')(), target=target)
            return

        if sentence.strip() in ['ls', 'jjk', ':wq', 'ifconfig']:
            self.chat('Wrong window.')
            return

        inquiries = [sentence.lower().find(t) != -1 for t in self.config.questions]

        if self.config.smartass and True in inquiries:
            # Naively parse out the question being asked
            try:
                smartassery = sentence.lower().split(self.config.questions[inquiries.index(True)])[1]
            except:
                return

            responses = self.config.ithelp

            # Dynamic cases need to be appended
            responses.append('http://lmgtfy.com/?q=' + smartassery.replace(' ', '+'))

            self.chat(random.choice(responses), target=target)
            return

        # There's a very good reason for this.
        if sentence == "oh shit its your birthday erikbeta happy birthday" and nick == "jcb":
            self._act(" slaps jcb")
            self.chat("LEAVE ERIK ALONE!", target=target)
            return


    @axon
    @help('WORD <Learn a word>')
    def learn(self):
        if not self.values: return "%s ponders the emptiness of meaning." % self.ego.nick
        if not re.match("^[A-Za-z]+$", self.values[0].strip()): return "%s doesn't think that's a word." % self.ego.nick

        open("%s/natwords" % self.cx.settings.directory.storage, 'a').write(self.values[0].strip() + '\n')
        self.chat("%s learn new word!" % self.ego.nick, self.lastsender)


    # I have this friend who kicks my ass in Scrabble
    # a lot. Being fairly obsessive, this is mostly
    # just to stop me from staring at the Scrabble app
    # over two or three days trying to find a bingo.
    # It's definitely still cheating, but it lets me
    # stop looking, and at the end of the day, keeping
    # my stress level down is more important than my
    # sense of honor.
    @axon
    @public
    @alias('scrabble')
    @help('LETTERS <cheat at Scrabble>')
    def scrabblecheat(self):
        if not self.values:
            return "Nothing to check"

        letters = sorted(self.values[0].lower())
        letters = ''.join(letters)

        matchlen = False if 'x' in self.flags else True
        truth = False if 'f' in self.flags else True

        words = []

        for line in open(self.config.scrabbledict):
            word = line.strip()
            if len(word) == 1: continue

            if matchlen and len(letters) != len(word): continue

            # TODO: account for wild cards :( may need regex

            test = ''.join(sorted(word))
            if test in letters:
                words.append(word)


        if truth and words:
            return 'Yup'

        if truth and not words:
            return 'Nope'

        if not words:
            return 'Nothing found'

        return ', '.join(words)


    @axon
    @help('ACRONYM <decide the words for an acronym>')
    def acronym(self):
        if not self.values:
            return "About what?"

        if not re.match("^[A-Za-z]+$", self.values[0]) \
        and self.lastsender == "erikbeta":
            return "Fuck off erik."

        if not re.match("^[A-Za-z]+$", self.values[0]):
            return "%s no want to think about that." % self.ego.nick

        if self.values[0].lower() == "gross":
            return "Get Rid Of Slimey girlS"

        output = self.acronymit(self.values[0])
        return output


    def acronymit(self, base):
        acronym = list(base.upper())
        output = []

        wordbank = []
        for line in open("%s" % self.config.acronymlib):
            wordbank.append(line.strip())

        for letter in acronym:
            good = False
            while not good:
                word = choice(wordbank).capitalize()
                if word[:1] == letter:
                    output.append(word)
                    good = True

        return " ".join(output)


    # I don't remember why this got added, but
    # it's unfailingly awesome.
    @axon
    @help('WORD [WHICH_DEFINITION] <look up etymology of word>')
    def ety(self):
        if not self.values:
            return "Enter a word"

        word = self.values[0]
        params = {'allowed_in_frame': '0', 'searchmode': 'term', 'search': word}

        request = Browser("http://www.etymonline.com/index.php", params)
        if not request:
            return 'Error'

        cont = request.soup()

        heads = cont.findAll("dt")
        defs = cont.findAll("dd")

        if not len(defs):
            return "Couldn't find anything"

        try:
            ord = int(self.values[1])
        except:
            ord = 1

        if ord > len(defs):
            ord = 1

        ord -= 1
        if ord < 0:
            ord = 0

        try:
            _word = ''.join(heads[ord].findAll(text=True))
            _def = ''.join(defs[ord].findAll(text=True))
        except Exception as e:
            self.chat('Failed to parse.', error=e)
            return

        return "Etymology %s of %s for %s: %s" % (str(ord + 1), str(len(defs)), _word, _def)


    @axon
    @help('WORD_OR_PHRASE <look up anagram>')
    def anagram(self):
        if not self.values:
            return "Enter a word or phrase"


        word = ''.join(self.values)
        url = 'http://www.anagramica.com/best/%s' % word

        request = Browser(url)
        if not request:
            return 'Error'

        try:
            json = request.json()
            return json['best']
        except Exception as e:
            self.chat("Couldn't parse.", str(e))
            return

    # http://emalmi.kapsi.fi/battlebot/battlebot.fcgi?l=en&q=tame%20it%20before%20you%20lose%20it
    @axon
    @help('LINE <get phat rhymes>')
    def rhyme(self):
        if not self.values:
            return "Enter a line"

        url = "http://emalmi.kapsi.fi/battlebot/battlebot.fcgi"
        params = "l=en&q=" + '+'.join(self.values)

        request = Browser('%s?%s' % (url, params))

        try:
            json = request.json()
            rhyme = choice(json["rhymes"])
            return rhyme['line']
        except Exception as e:
            self.chat('...')
            self._act("drops mic in shame.")
            return

    # This pair of gems was created because Elliott kept
    # piping .all to various * commands.
    @axon
    def shutup(self):
        self.chat('Shutting up now.')
        self.cx.bequiet = True
        return


    @axon
    def speakup(self):
        self.cx.bequiet = False
        return 'Back.'


    @axon
    def spoonerize(self):
        if not self.values:
            return 'Spoonerize what?'
        return 'http://mongobot.com/spoon/%s' % self.values[0]

