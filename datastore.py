import mongoengine
from mongoengine import *


def connectdb():
    mongoengine.connect('bot', 'bot')


class Position(mongoengine.EmbeddedDocument):
    symbol = StringField(required=True)
    date = DateTimeField(required=True)
    price = FloatField(min_value=0)
    quantity = IntField(min_value=0)
    type = StringField()


class Drinker(mongoengine.Document):
    name = StringField(required=True)
    company = StringField()

    cash = FloatField(default=100000)
    positions = ListField(EmbeddedDocumentField(Position))


class Words(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)
    definition = StringField(required=True)
    source = StringField(required=True)


class Learned(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)


class Structure(mongoengine.Document):
    structure = ListField(StringField())
    contents = ListField(StringField())
