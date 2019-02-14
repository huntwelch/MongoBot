from autonomic import axon, alias, help, Dendrite, Cerebellum, Synapse, Receptor
from staff import Browser
from random import randint, choice
from util import csscolors


kittalims = {
    'glasses': 8,
    'toy': 19,
    'hat': 12,
}

# name[special]
specials = [
    'space',
]

bgcolors = [
	'bg-light-blue',
	'bg-red',
	'bg-blue',
	'bg-light-purple',
	'bg-purple',
	'bg-green',
	'bg-teal',
	'bg-yellow',
	'bg-mauve',
]

catcolors = [
	'cat-grey',
	'cat-orange',
	'cat-white',
	'cat-black',
]

kitties = [
	'frisky',
	'scuba',
    'unicorn',
    'camper',
    'rocketship',
    'fan',
    'bonsai',
    'midi',
    'coffee',
]

@Cerebellum
class Tabbycats(Dendrite):

    def __init__(self, cortex):
        super(Tabbycats, self).__init__(cortex)

    @axon
    @help("<Generate kittah>")
    def tabby(self):
        data = {
        	'likesPets':False,
        	'name[first]':'Das',
        	'name[last]':'Cat',
        	'name[full]':'Das Cat',
        	'body':randint(0,5),
        	'head':randint(0,1),
        	'color[background]':choice(bgcolors),
        	'color[cat]':choice(catcolors),
        	'activeGoodies[hat]':'hat-%s' % randint(1, kittalims['hat']),
        	'activeGoodies[glasses]':'glasses-%s' % randint(1, kittalims['glasses']),
        	'activeGoodies[toy]':'toy-%s' % randint(1, kittalims['toy']),
        	'kitty': 'no-kitty' if randint(0, 4) != 4 else choice(kitties),
        }

        catid = Browser('http://tabbycats.club/save', params=data, method='POST')
        link = 'http://tabbycats.club/%s' % catid.read()

        return link


