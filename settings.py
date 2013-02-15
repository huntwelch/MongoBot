from math import *
from secrets import CHANNEL

# Connection Settings

HOST = "irc.freenode.net"
PORT = 6667
NICK = "MongoBot"

# These settings are set in secrets.py

# CHANNEL = (str) irc channel
# WORDNIK_API = (str) for wordnik calls
# WEATHER_API = (str) for weather calls to wunderground.com
# SQL_PASSWORD = duh

# Directory settings

STORAGE = "hippocampus"
LOGDIR = STORAGE + "/log"
LOG = LOGDIR + "/chat.log"
DISTASTE = STORAGE + "/distaste"
ACROSCORE = STORAGE + "/acro/"

# Misc

CONTROL_KEY = "-"
SHORTENER = "http://roa.st/api.php?roast="
PATIENCE = 7000
REPO = "https://github.com/huntwelch/MongoBot"
BANNED = []
USERS = [
    'castr0',
    'chiyu',
    'chiyou',
    'chiyou_',
    'dcross2',
    'digx',
    'erikbeta',
    'jcb',
    'jsbronder',
    'kenfree',
    'loxo33',
    'melanarchy',
    'mirotame',
    'realvinay',
    'sublimnl',
    'Viza',
    'woxidu',
    'woxidu_home',
    'xtrium',
    'Euj1',
]
# Acro

ACROLIB = "natwords"
MINLEN = 5
MAXLEN = 7
ROUNDS = 5
ROUNDTIME = 120
WARNING = 30
VOTETIME = 30
MIN_PLAYERS = 3
TIME_FACTOR = 2
NO_ACRO_PENALTY = 2
NO_VOTE_PENALTY = 5
BREAK = 15
BOTPLAY = True

IDENT = "macrotic"
REALNAME = "macrotic"
OWNER = "chiyou"

SAFESET = [
    ('Bot settings', ':'),
    ('CONTROL_KEY', '"' + CONTROL_KEY + '"'),
    ('SHORTENER', '"' + SHORTENER + '"'),
    ('PATIENCE', PATIENCE),
    ('NICK', '"' + NICK + '"'),
    ('CHANNEL', '"' + CHANNEL + '"'),
    ('HOST', '"' + HOST + '"'),
    ('PORT', PORT),

    ('Acro settings', ':'),
    ('ACROLIB', ACROLIB),
    ('MINLEN', MINLEN),
    ('MAXLEN', MAXLEN),
    ('ROUNDS', ROUNDS),
    ('ROUNDTIME', ROUNDTIME),
    ('WARNING', WARNING),
    ('VOTETIME', VOTETIME),
    ('MIN_PLAYERS', MIN_PLAYERS),
    ('NO_ACRO_PENALTY', NO_ACRO_PENALTY),
    ('NO_VOTE_PENALTY', NO_VOTE_PENALTY),
    ('BREAK', BREAK),
    ('BOTPLAY', BOTPLAY),
]

INSULTS = [
    "are little bitches",
    "are chumps",
    "are cunt knockers",
    "are lazy bastards",
    "are busy with dcross's mom",
]

INSULT = [
    "is a little bitch",
    "is a chump",
    "is a cunt knocker",
    "is a lazy bastard",
    "is busy with dcross's mom",
]

BOREDOM = [
    "kicks",
    "slaps",
    "butt rapes",
    "offers dcross's mom to",
    "throws feces at",
]

SAFE = [
    ('abs', abs),
    ('acos', acos),
    ('asin', asin),
    ('atan', atan),
    ('atan2', atan2),
    ('ceil', ceil),
    ('cos', cos),
    ('cosh', cosh),
    ('degrees', degrees),
    ('e', e),
    ('exp', exp),
    ('fabs', fabs),
    ('floor', floor),
    ('fmod', fmod),
    ('frexp', frexp),
    ('hypot', hypot),
    ('ldexp', ldexp),
    ('log', log),
    ('log10', log10),
    ('modf', modf),
    ('pi', pi),
    ('pow', pow),
    ('radians', radians),
    ('sin', sin),
    ('sinh', sinh),
    ('sqrt', sqrt),
    ('tan', tan),
    ('tanh', tanh),
]

RM_URL = ""
RM_USERS = dict(
    hunt={"id": "89"},
)
