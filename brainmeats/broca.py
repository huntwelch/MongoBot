import wordnik
import mongoengine
import nltk
import re
import string 

from autonomic import axon, category, help, Dendrite
from secrets import WORDNIK_API
from settings import NICK, STORAGE, ACROLIB
from datastore import Words, Learned, Structure
from random import choice
from util import pageopen
from BeautifulSoup import BeautifulSoup as soup


@category("language")
class Broca(Dendrite):
    def __init__(self, cortex):
        super(Broca, self).__init__(cortex)

    @axon
    @help("[word] <get definition of word>")
    def whatmean(self):
        self.snag()

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
            self.seekdef(word)
            return

        self.chat(str(len(self.definitions)) + " definitions for " + word)
        self.chat("Definition " + str(which + 1) + ": " + definition)

    def seekdef(self, word):
        wapi = wordnik.Wordnik(api_key=WORDNIK_API)
        results = wapi.word_get_definitions(word.strip())
        count = 0
        for item in results:
            try:
                definition = Words(word=item["word"],
                                   partofspeech=item["partOfSpeech"],
                                   definition=item["text"],
                                   source=item["sourceDictionary"])
                definition.save()
                if count == 0:
                    tempdef = item["text"]

                count += 1
            except:
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

    def tourettes(self, sentence, nick):
        if re.search("^" + NICK, sentence):
            backatcha = sentence[len(NICK):]
            self.chat(nick + "'s MOM" + backatcha)
            return

        if "mom" in sentence.translate(string.maketrans("", ""), string.punctuation).split():
            open(LOGDIR + "/mom.log", 'a').write(sentence + '\n')
            return

        if sentence.lower().find("oh snap") != -1:
            self.chat("yeah WHAT?? Oh yes he DID")
            return

        if sentence.lower().find("rimshot") != -1:
            self.chat("*ting*")
            return

        if sentence.lower().find("stop") == len(sentence) - 4 and len(sentence) != 3:
            self.chat("Hammertime")
            return

    @axon
    @help("<command " + NICK + " to speak>")
    def speak(self):
        sentence = []
        struct = choice(Structure.objects())
        for pos in struct.structure:
            _word = choice(Learned.objects(partofspeech=pos))
            sentence.append(_word.word)

        self.chat(" ".join(sentence))

    @axon
    @help("<teach " + NICK + " a word>")
    def learn(self):
        self.snag()

        # TODO: put banned in settings
        banned = []
        if self.lastsender in banned:
            self.chat("My daddy says not to listen to you.")
            return

        if not self.values:
            self.chat(NICK + " ponders the emptiness of meaning.")
            return

        if not re.match("^[A-Za-z]+$", self.values[0].strip()):
            self.chat(NICK + " doesn't think that's a word.")
            return

        open(STORAGE + "/natwords", 'a').write(self.values[0].strip() + '\n')
        self.chat(NICK + " learn new word!", self.lastsender)

    @axon
    @help("<have " + NICK + " create an acronym>")
    def think(self):
        self.snag()

        if not self.values:
            self.chat("About what?")
            return

        if not re.match("^[A-Za-z]+$", self.values[0]) and self.lastsender == "erikbeta":
            self.chat("Fuck off erik.")
            return

        if not re.match("^[A-Za-z]+$", self.values[0]):
            self.chat(NICK + " no want to think about that.")
            return

        output = self.acronymit(self.values[0])
        self.chat(output)

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
    @help("word [which def] <look up etymology of word>")
    def ety(self):
        self.snag()

        if not self.values:
            self.chat("Enter a word")
            return

        word = self.values[0]
        url = "http://www.etymonline.com/index.php?allowed_in_frame=0&search=" + word + "&searchmode=term"

        urlbase = pageopen(url)
        if not urlbase:
            self.chat("Couldn't find anything")
            return

        cont = soup(urlbase)

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

        _word = ''.join(heads[ord].findAll(text=True)).encode("utf-8")
        _def = ''.join(defs[ord].findAll(text=True)).encode("utf-8")

        self.chat("Etymology " + str(ord + 1) + " of " + str(len(defs)) +
                  " for " + _word + ": " + _def)

    # TODO: broken, not sure why
    @axon
    @help("word_or_phrase <look up anagram>")
    def anagram(self):
        self.snag()

        if not self.values:
            self.chat("Enter a word or phrase")
            return

        word = '+'.join(self.values)
        url = "http://wordsmith.org/anagram/anagram.cgi?anagram=" + word + "&t=50&a=n"

        urlbase = pageopen(url)
        if not urlbase:
            self.chat("Couldn't find anything")
            return

        cont = soup(urlbase)

        paragraph = cont.findAll("p")[4]
        content = ''.join(paragraph.findAll()).replace("<br/>", ", ").encode("utf-8")
        self.chat(content)
