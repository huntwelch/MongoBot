import wordnik
import mongoengine
from mongoengine import *
from settings import *


class Words(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)
    definition = StringField(required=True)
    source = StringField(required=True)


class Broca():

    def __init__(self, mongo):
        self.mongo = mongo
        mongoengine.connect('bot', 'bot', 'asdfqwer')

    def whatmean(self):

        if not self.mongo.values:
            self.mongo.chat("Ooohhhmmmmm")
            return

        word = self.mongo.values[0]
        which = 0

        self.definitions = Words.objects(word=word)

        if len(self.mongo.values) == 2:
            try:
                which = int(self.mongo.values[1]) - 1
            except:
                self.mongo.chat("Invalid index. Defaulting to 1.")

        try:
            definition = self.definitions[which]["definition"]
        except:
            self.mongo.chat("Can't find a definition. Pinging wordnik...")
            self.seekdef(word)
            return

        self.mongo.chat(str(len(self.definitions)) + " definitions for " + word)
        self.mongo.chat("Definition " + str(which + 1) + ": " + definition)

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
            self.mongo.chat("Wordnik coughed up " + str(count) + " definitions.")
            self.mongo.chat("Definition 1:" + tempdef)
        else:
            self.mongo.chat("I got nothin.")
