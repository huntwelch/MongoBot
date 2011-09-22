from math import *

# Connection Settings
 
HOST = "irc.freenode.net"
PORT = 6667
NICK = "MongoBot"
CHANNELINIT = "#okdrink"
              
# Misc

SHORTENER = "http://roa.st/api.php?roast="

# Acro

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

# STOP 

IDENT = "macrotic" 
REALNAME = "macrotic"
OWNER = "chiyu"

# Directory settings

BRAIN = "mongo-brain"
LOG = BRAIN + "/mongo.log"
DISTASTE = BRAIN + "/distaste"
ACROSCORE = BRAIN + "/acro/"
ACROLIB = "natwords"
 
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
    ('tanh',tanh),
]

