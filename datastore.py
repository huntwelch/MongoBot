import mongoengine
from mongoengine import *


def connectdb():
    mongoengine.connect('bot', 'bot')
    

class Drinker(mongoengine.Document):
    name = StringField(required = True)
    company = StringField()
    portfolio = ListField(StringField(max_length=8))


