import wordnik
import mongoengine
from mongoengine import *
from time import sleep

WORDNIK_API = "62d747d2294f2fda6112d43604f273e0aefd2d839a2c257c9"
wapi = wordnik.Wordnik(api_key=WORDNIK_API)

mongoengine.connect('bot','bot','asdfqwer')

class Words(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)
    definition = StringField(required=True)
    source = StringField(required=True)

iter = 0
entries = 0
cutpoint = False
record = True 
for line in open("mongo-brain/wordbank"):
    if not record:
        if cutpoint and line.strip() == cutpoint:
            record = True
        continue
    sleep(1)
    results = wapi.word_get_definitions(line.strip())
    iter += 1

    for item in results:
        try:
            definition = Words(word=item["word"],
                               partofspeech=item["partOfSpeech"],  
                               definition=item["text"],  
                               source=item["sourceDictionary"])
            definition.save()
        except:
            print "FAIL: " + line.strip() + " -- " + str(results)
        entries += 1

    print line.strip() + " defined. #" + str(iter) + " (" + str(entries) + ")"
    

