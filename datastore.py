import mongoengine
from mongoengine import *


def connectdb():
    mongoengine.connect('bot', 'bot')
    

class Drinker(mongoengine.Document):
    name = StringField(required = True)
    company = StringField()
    portfolio = ListField(StringField(max_length=8))


class Words(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)
    definition = StringField(required=True)
    source = StringField(required=True)

class Learned(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)

class Structure(mongoengine.Document):
    structure  = ListField(StringField())
    contents = ListField(StringField())
