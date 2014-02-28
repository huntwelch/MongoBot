import mongoengine
import nltk
import re
import string
import random
import redis
import time
import os
import simplejson

from threading import Thread
from autonomic import axon, alias, help, Dendrite
from secrets import WORDNIK_API
from settings import NICK, STORAGE, ACROLIB, LOGDIR, BOOKS, BABBLE_LIMIT, \
    REDIS_SOCK, SMARTASS, TECH_QUESTIONS, IT_HELP, FRUSTRATION, POEMS, \
    WEBSITE
from datastore import Words, Learned, Structure
from random import choice, randint
from util import savefromweb, Browse
from bs4 import BeautifulSoup as bs4
from wordnik import swagger, WordApi


# Much fail here. I study up on NLTK at the rate
# of 5 minutes a month. The miscellaneous language 
# functions usually work, and of course the markov
# is done here.
class Broca(Dendrite):

    markov = redis.StrictRedis(unix_socket_path=REDIS_SOCK) 
    readstuff = False
    knowledge = False
    draft = False

    def __init__(self, cortex):
        super(Broca, self).__init__(cortex)

    @axon
    @help('TITLE <have %s compose poetry>' % NICK)
    def compose(self):
        if not self.startpoem():
            return 'Already wrote that'

        poem = ''
        seed = self.babble()

        if not seed:
            return 'Muse not with %s today' % NICK

        seed = seed.split()
        for word in seed:
            poem += ' ' + self.babble([word])
        
        self.addtext(poem.split())

        return self.finis()
        

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

        if os.path.isfile(POEMS + filename):
            self.chat('Already wrote that')
            return False

        draft = open(POEMS + filename, 'a') 
        draft.write('%s\n' % title)
        draft.close()

        self.draft = filename

        return '%s think "%s" may be masterpiece' % (NICK, title)

    @axon
    @alias('write', 'explicit')
    def addtext(self, what=False):

        # TODO: calling with -explicit will disable random line breaks

        if not self.draft:
            return 'No poems open now.'
        
        draft = open(POEMS + self.draft, 'a') 

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
        link = '%s/poem/%s' % (WEBSITE, self.draft[:-4])
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
    @help("URL_OF_TEXT_FILE <Make " + NICK + " read something>")
    def read(self):
        if not self.values:
            self.chat("Read what?")
            return

        book = self.values[0]
        if book[-4:] != '.txt':
            self.chat("Plain text file only. %s purist." % NICK)
            return

        name = "%s_%s.txt" % ( int(time.mktime(time.localtime())), self.lastsender )
        path = BOOKS + name

        def comfychair(book, path):
            savefromweb(book, path)    
            with open(path) as b:
                for line in b:
                    self.mark(line)

        self.chat('Pulling up a chair...')
        self.butler.do('Eh, I like his older, funnier work.', comfychair, (book, path))

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
    @alias('waxrhapsodic')
    @help('<Make %s speak markov chain>' % NICK)
    def babble(self, what=False):

        what = what or self.values

        if what:
            if len(what) > 1:
                pattern = "%s %s" % (what[0], what[1])
            else:
                pattern = "*%s*" % what[0]

            matches = self.markov.keys(pattern)

            if not matches:
                self.chat('Got nothin')
                return

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
            'its', 'of', 'is',
        ]

        while len(words) < BABBLE_LIMIT:
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
        words = ' '.join(words)

        return words

    # This is kind of sluggish and kldugey,
    # and sort of spiritually been replaced by
    # the read function above.
    #
    # @axon
    # def readup(self):
    #     if self.knowledge:
    #         self.chat("Already read today.")
    #         return

    #     self.chat("This may take a minute.")
    #     books = open(RAW_TEXT, 'r')
    #     data = books.read().replace('\n', ' ')
    #     tokens = nltk.word_tokenize(data)
    #     self.knowledge = nltk.Text(tokens)

    #     self.chat("Okay, read all the things.")

    @axon
    @help("<command " + NICK + " to speak>")
    def speak2(self):
        if not self.knowledge:
            self.chat("Can't speak good yet. Must read.")
            return

        if not self.readstuff:
            self.chat("Just one sec...")
            self.knowledge.generate()

        length = randint(10, 100)
        text = ' '.join(self.knowledge._trigram_model.generate(length))

        self.readstuff = True
        self.chat(text)

    @axon
    @help("WORD <get definition of word>")
    def whatmean(self):
        if not self.values:
            self.chat("Ooohhhmmmmm")
            return

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
        if not WORDNIK_API:
            self.chat("WORDNIK_API is not set.")
            return

        client = swagger.ApiClient(WORDNIK_API, 'http://api.wordnik.com/v4')
        wapi = WordApi.WordApi(client)
        results = wapi.getDefinitions(word.strip())

        count = 0

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
            self.chat("I got nothin.")

    def parse(self, sentence, nick):
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        structure = []
        contents = []
        for word, type in tagged:
            records = Learned.objects(word=word)
            if not records:
                record = Learned(word=word, partofspeech=type)
                try:
                    record.save()
                except:
                    pass

            try:
                structure.append(type)
                contents.append(word)
            except:
                pass

        try:
            struct = Structure(structure=structure, contents=contents)
            struct.save()
        except:
            pass

    # This is where all the conversational tics and 
    # automatic reactions are set up. Also, for some
    # reason, the mom log, because it's awesome but
    # maybe not cortex material. Is the name of this
    # function in poor taste? Yes.
    def tourettes(self, sentence, nick):
        if "mom" in sentence.translate(string.maketrans("", ""), string.punctuation).split():
            open(LOGDIR + "/mom.log", 'a').write(sentence + '\n')

        if re.search("^" + NICK, sentence):
            backatcha = sentence[len(NICK):]
            self.chat(nick + "'s MOM" + backatcha)
            return

        if sentence.lower().find("oh snap") != -1:
            self.chat("yeah WHAT?? Oh yes he DID")
            return

        if sentence.lower().find("murican") != -1:
            self.chat("fuck yeah")
            return

        if sentence.lower().find("rimshot") != -1:
            self.chat("*ting*")
            return

        if sentence.lower().find("stop") == len(sentence) - 4 and len(sentence) != 3:
            stops = [
                'Hammertime',
                "Children, what's that sound",
                'Collaborate and listen',
            ]
            self.chat(random.choice(stops))
            return

        if sentence.lower().strip() in FRUSTRATION or sentence.lower().find('stupid') == 0:
            self.chat(self.cx.commands.get('table')())

        inquiries = [sentence.lower().find(t) != -1 for t in TECH_QUESTIONS]
        
        if SMARTASS and True in inquiries:
            # Naively parse out the question being asked
            try:
                smartassery = sentence.lower().split(TECH_QUESTIONS[inquiries.index(True)])[1]
            except:
                return

            responses = IT_HELP

            # Dynamic cases need to be appended
            responses.append('http://lmgtfy.com/?q=' + smartassery.replace(' ', '+'))
                
            self.chat(random.choice(responses))
            return

        # There's a very good reason for this.
        if sentence == "oh shit its your birthday erikbeta happy birthday" and self.lastsender == "jcb":
            self._act(" slaps jcb")
            self.chat("LEAVE ERIK ALONE!")
            return

    @axon
    @help("<command %s to speak>" % NICK)
    def speak(self):
        sentence = []
        struct = choice(Structure.objects())
        for pos in struct.structure:
            _word = choice(Learned.objects(partofspeech=pos))
            sentence.append(_word.word)

        self.chat(" ".join(sentence))

    @axon
    @help("WORD <teach %s a word>" % NICK)
    def learn(self):
        if not self.values:
            self.chat(NICK + " ponders the emptiness of meaning.")
            return

        if not re.match("^[A-Za-z]+$", self.values[0].strip()):
            self.chat(NICK + " doesn't think that's a word.")
            return

        open(STORAGE + "/natwords", 'a').write(self.values[0].strip() + '\n')
        self.chat(NICK + " learn new word!", self.lastsender)

    @axon
    @help("ACRONYM <have %s decide the words for an acronym>" % NICK)
    def acronym(self):
        if not self.values:
            self.chat("About what?")
            return

        if not re.match("^[A-Za-z]+$", self.values[0]) and self.lastsender == "erikbeta":
            self.chat("Fuck off erik.")
            return

        if not re.match("^[A-Za-z]+$", self.values[0]):
            self.chat(NICK + " no want to think about that.")
            return

        if self.values[0].lower() == "gross":
            self.chat("Get Rid Of Slimey girlS")
            return

        output = self.acronymit(self.values[0])
        return output

    def acronymit(self, base):
        acronym = list(base.upper())
        output = []

        wordbank = []
        for line in open(STORAGE + "/" + ACROLIB):
            wordbank.append(line.strip())

        for letter in acronym:
            good = False
            while not good:
                word = choice(wordbank).capitalize()
                if word[:1] == letter:
                    output.append(word)
                    good = True

        return " ".join(output)

    @axon
    @help("WORD [WHICH_DEFINITION] <look up etymology of word>")
    def ety(self):
        if not self.values:
            self.chat("Enter a word")
            return

        word = self.values[0]
        params = {'allowed_in_frame': '0', 'searchmode': 'term', 'search': word}

        site = Browse("http://www.etymonline.com/index.php", params)
        if site.error:
            self.chat(site.error)
            return

        cont = bs4(site.read())

        heads = cont.findAll("dt")
        defs = cont.findAll("dd")

        if not len(defs):
            self.chat("Couldn't find anything")
            return

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


    # TODO: broken, not sure why
    @axon
    @help("WORD_OR_PHRASE <look up anagram>")
    def anagram(self):
        if not self.values:
            self.chat("Enter a word or phrase")
            return

        word = ''.join(self.values)
        url = 'http://www.anagramica.com/best/%s' % word

        site = Browse(url)
        if site.error:
            self.chat(site.error)
            return

        try:
            json = simplejson.loads(site.read())
            return json['best']
        except Exception as e:
            self.chat("Couldn't parse.", str(e))
