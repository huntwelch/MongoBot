import mongoengine

from mongoengine import *
from settings import STARTING_CASH

# All mongodb stuff.

def connectdb():
    mongoengine.connect('bot', host='localhost')


def simpleupdate(whom, key, val):
    try:
        drinker = Drinker.objects(name=whom)
        if drinker:
            drinker = drinker[0]
        else:
            drinker = Drinker(name=whom)

        drinker[key] = val
        drinker.save()
    except:
        return False

    return True


def incrementEntity(whom, amount):
    try:
        entity = Entity.objects(name=whom)
        if entity:
            entity = entity[0]
        else:
            entity = Entity(name=whom)

        if entity.value:
            entity.value = entity.value + amount
        else:
            entity.value = 0 + amount
    except:
        return False
    entity.save()
    return True


def entityScore(whom):
    try:
        entity = Entity.objects(name=whom)
        if entity:
            entity = entity[0]
        else:
            entity = Entity(name=whom)
    except:
        return 0
    return entity.value

def topScores(limit):
    return Entity.objects.order_by('-value').limit(limit)

class Entity(mongoengine.Document):
    name = StringField(required=True)
    value = IntField(default=0)


class Position(mongoengine.EmbeddedDocument):
    symbol = StringField(required=True)
    date = DateTimeField(required=True)
    price = FloatField(min_value=0)
    quantity = IntField(min_value=0)
    type = StringField()


class Drinker(mongoengine.Document):
    name = StringField(required=True)
    password = StringField(min_length=40, max_length=40)
    company = StringField()
    phone = StringField()
    rewards = IntField(default=0)
    awaiting = StringField()
    cash = FloatField(default=STARTING_CASH)
    positions = ListField(EmbeddedDocumentField(Position))


class Words(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)
    definition = StringField(required=True)
    source = StringField(required=True)


class Markov(mongoengine.Document):
    prefix = StringField()
    follow = ListField(StringField())


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
