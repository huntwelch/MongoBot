import mongoengine
from mongoengine import *
from settings import STARTING_CASH


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
    awaiting = StringField()
    cash = FloatField(default=STARTING_CASH)
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

class Quote(mongoengine.Document):
    date = DateTimeField(required=True)
    text = StringField(required=True)
    adder = StringField(required=True)
    random = FloatField()

    meta = {
        'indexes': ['random', 'text', ('text', 'random')]
    }
