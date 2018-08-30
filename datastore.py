import mongoengine

from mongoengine import *
import sys, traceback

# All mongodb stuff. I've been told this would be
# better done with sqlite. Some day.

def connectdb():
    mongoengine.connect('bot', host='localhost')


def simpleupdate(whom, key, val, crement=False):
    try:
        drinker = Drinker.objects(name=whom)
        if drinker:
            drinker = drinker[0]
            # Incoming epic cheat
            if crement:
                if 'cash' not in drinker['data']:
                    drinker['data']['cash'] = 0
                drinker['data']['cash'] = drinker['data']['cash'] + val
                # *sigh*
            else:
                drinker[key] = val
            drinker.save()
        else:
            incrementEntity(whom, val)

    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return False

    return True


def incrementEntity(whom, amount):
    amount = int(amount)
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
        drinker = Drinker.objects(name=whom)
        if drinker:
            drinker = drinker[0]
            value = drinker['data']['cash']
        else:
            entity = Entity.objects(name=whom)
            entity = entity[0]
            value = entity.value
    except:
        return 0
    return value


def topScores(limit):
    return Entity.objects.order_by('-value').limit(limit)


class Entity(mongoengine.Document):
    name = StringField(required=True)
    value = IntField(default=0)
    meta = {'strict': False}


class Alias(mongoengine.EmbeddedDocument):
    name = StringField(required=True)
    definition = StringField(required=True)
    meta = {'strict': False}


class Defaults(mongoengine.Document):
    command = StringField(required=True)
    response = StringField(required=True)
    meta = {'strict': False}


class Position(EmbeddedDocument):
    symbol = StringField(required=True)
    date = DateTimeField(required=True)
    price = FloatField(min_value=0)
    quantity = IntField(min_value=0)
    type = StringField()
    meta = {'strict': False}


class Drinker(mongoengine.Document):
    name = StringField(required=True)
    password = StringField(min_length=64, max_length=64)
    idents = ListField(StringField(), default=list)
    company = StringField()
    phone = StringField()
    rewards = IntField(default=0)
    awaiting = StringField()
    cash = FloatField(default=100000)
    positions = ListField(EmbeddedDocumentField(Position))
    aliases = ListField(EmbeddedDocumentField(Alias))
    data = DictField()
    meta = {'strict': False}


class Words(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)
    definition = StringField(required=True)
    source = StringField(required=True)
    meta = {'strict': False}


class Learned(mongoengine.Document):
    word = StringField(required=True)
    partofspeech = StringField(required=True)
    meta = {'strict': False}


class Structure(mongoengine.Document):
    structure = ListField(StringField())
    contents = ListField(StringField())
    meta = {'strict': False}


class Quote(mongoengine.Document):
    date = DateTimeField(required=True)
    text = StringField(required=True)
    adder = StringField(required=True)
    random = FloatField()

    meta = {
        'indexes': ['random', 'text', ('text', 'random')],
        'strict': False,
    }
