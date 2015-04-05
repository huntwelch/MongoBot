import mongoengine

from mongoengine import *


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
                drinker['data']['cash'] = drinker['data']['cash'] + val
                # *sigh*
            else:
                drinker[key] = val
            drinker.save()
        else:
            incrementEntity(whom, val)

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
        drinker = Drinker.objects(name=whom)
        if drinker:
            drinker = drinker[0]
            value = drinker['data']['cash']
        else:
            enitity = Entity.objects(name=whom)
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


class Alias(mongoengine.EmbeddedDocument):
    name = StringField(required=True)
    definition = StringField(required=True)


class Defaults(mongoengine.Document):
    command = StringField(required=True)
    response = StringField(required=True)


class Position(EmbeddedDocument):

    symbol = StringField(required=True)
    date = DateTimeField(required=True)
    price = FloatField(min_value=0)
    quantity = IntField(min_value=0)
    type = StringField()


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
