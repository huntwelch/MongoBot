import collections

from random import SystemRandom

from autonomic import axon, alias, help, Dendrite, Cerebellum, Synapse, Receptor, autocommand
from util import colorize
from datastore import simpleupdate

# Today, 3/24/2015 is Danny O'Shea's birthday.
# In honor of it, today is the day I implement
# the gambling dice game he taught me at the
# the very bar I'm sitting at, where a white
# Polish dude is telling a racist joke to the
# black bartender, who has no patience for it.
@Cerebellum
class Farkle(Dendrite):
    limit = 1000
    turn = 0
    min = 0
    scoring = 0
    score = 0
    broke = False
    players = {}
    scoredice = []
    playerorder = []

    top = 0
    winner = None

    # Would be nice, but the dice are pathetically
    # small and hard to see.
    prettydice = [
        u'\u2680',
        u'\u2681',
        u'\u2682',
        u'\u2683',
        u'\u2684',
        u'\u2685',
    ]


    def __init__(self, cortex):
        super(Farkle, self).__init__(cortex)


    @axon
    @help('<show rules for dice game>')
    def dicerules(self):
        rules = [
            '.toss to roll',
            '1s are 100, 5s are 50, 3 of a kind is die value * 100, except 3 ones, which is 1000',
            'An initial roll consisting of (1 2 3 4 5) in any order is 500',
            'You can keep rolling as long as you keep one scoring die or triplet',
            '.toss automatically roles your non-scoring dice. If you want to roll more, specify with .toss 3',
            'If you roll without scoring, you lose all points and your turn is over',
            'If all your dice are scoring, you clear and must roll again, keeping your points so far',
            'Otherwise you can stop whenever you want with .takeit',
            'Once somebody breaks the limit, everybody else gets one more chance to top their score',
            'Highest score wins',
        ]

        return rules


    @axon
    @help('LIMIT <set the the score ceiling>')
    def setlimit(self):
        if self.players:
            return "Can't change limit mid game"
        if not self.values:
            return "Specify limit"
        try:
            self.limit = int(self.values[0])
        except:
            return "Something wasn't right there"

        return "Limit set to %s" % self.limit


    @axon
    @help('<show current scores>')
    def dicescore(self):
        if not self.players:
            return 'Nobody playing'
        for player in self.players:
            self.chat('%s: %s' % (player, self.players[player]['score']))
        self.chat('Ceiling is %s' % self.limit)


    @axon
    @help('<join or return to dice game>')
    @alias('joindice')
    def joinup(self, _name=None):
        name = _name or self.lastsender

        if not _name and self.broke:
            return "No new players after the limit's broken"

        if name in self.playerorder and not _name:
            return 'You already in bro'

        if name in self.playerorder: return

        self.playerorder.append(name)

        if name in self.players and not _name:
            return 'You back'

        self.players[name] = {
            'score': 0,
            'broke': False,
        }

        if not _name:
            return 'You in'


    @axon
    @help('<leave the dice game>')
    def quitdice(self):
        if not self.playerorder:
            return "Nobody playing"

        if self.turn > self.playerorder.index(self.lastsender):
            self.turn -= 1

        self.playerorder.remove(self.lastsender)
        return "Yer out"


    @axon
    def activedice(self):
        return ', '.join(self.playerorder) or "Nobody playing"

    @axon
    @help("[HOW_MANY] <roll dem dice>")
    def toss(self):

        if self.lastsender not in self.players and self.broke:
            return "No new players after the limit's broken"

        self.joinup(self.lastsender)
        if self.playerorder[self.turn] != self.lastsender:
            return "Not your turn"


        rolling = 5 - self.scoring

        if self.values:
            try:
                rolling = int(self.values[0])
            except:
                return "Don't roll like that"

        if rolling > (5 - self.min):
            return "You have %s dice to roll." % (5 - self.min)

        if self.scoring == 0:
            rolling = 5

        # Apply last roll score after determining how many
        # dice got picked back up. Maybe better done with a
        # pendingscore variable but this works.
        if self.scoredice:
            self.scoring = len(self.scoredice[:-rolling])
            self.scoredice = self.scoredice[:-rolling]
            score, scoredice, scoring, min, triple = self.getscore(self.scoredice)
            self.score += score

        result = self.roll(rolling)

        score, scoredice, scoring, min, triple = self.getscore(result)
        self.scoredice.extend(scoredice)

        busted = False
        message = 'and rolling'
        color = None
        if scoring == 0:
            self.turn = (self.turn + 1) % len(self.playerorder)
            message = 'and bust.'

            if not self.players[self.playerorder[self.turn]]['broke']:
                message += ' %s to roll.' % self.playerorder[self.turn]

            self.score = 0
            busted = True
            color = 'red'
        if scoring == rolling:
            message = 'and clear!'
            self.score += score
            color = 'lightcyan'


        # Common resets
        if scoring in [0, rolling]:
            scoring = 0
            score = 0
            self.scoring = 0
            self.scoredice = []
            self.min = 0
            min = 0

        if self.scoredice:
            self.scoredice = sorted(scoredice)
            self.scoredice.extend([None] * (5 - len(self.scoredice)))

        self.scoring += scoring
        self.min += min

        if not color:
            display = [colorize(str(x), 'lightgreen') if x in [1,5, triple] else str(x) for x in result]
            message = '%s for %s %s' % (' '.join(display), score + self.score, message)
        else:
            message = '%s for %s %s' % (' '.join(str(s) for s in result), score + self.score, message)
            message = colorize(message, color)

        if not busted and self.broke:
            self.gethigh()
            total_now = self.players[self.playerorder[self.turn]]['score'] + score + self.score
            if total_now <= self.top:
                message += '. %s to go for the win.' % (self.top - total_now + 50)
            else:
                message += '. Winning with %s.' % total_now

        self.chat(message)
        if busted:
            self.checkwin()


    @axon
    @help("<Take your score>")
    @alias('keepit')
    def takeit(self):

        if not self.scoredice:
            return "You can't take it right now."

        if not self.playerorder:
            return "Nobody playing"

        if self.playerorder[self.turn] != self.lastsender:
            return "Not your turn"

        score, scoredice, scoring, min, triple = self.getscore(self.scoredice)
        self.score += score

        player = self.players[self.playerorder[self.turn]]
        player['score'] += self.score

        message = "%s takes it at %s for %s. " % (self.playerorder[self.turn], self.score, player['score'])

        if player['score'] >= self.limit and not self.broke:
            player['broke'] = True
            message += ' %s has been broken with %s! Last chance, people. ' % (self.limit, player['score'])
            self.broke = True

        self.turn = (self.turn + 1) % len(self.playerorder)

        if not self.players[self.playerorder[self.turn]]['broke']:
            message += '%s to roll.' % self.playerorder[self.turn]

        self.score = 0
        self.scoring = 0
        self.scoredice = []
        self.min = 0

        self.chat(message)
        self.checkwin()


    def roll(self, count):
        result = []
        while count:
            count -= 1
            random = SystemRandom()
            result.append(random.randint(1,6))

        # superfluous here, but handy if you switch
        # to quantum results
        result = [int(x) for x in result]

        return result
        # Weirdly these numbers didn't seem super random. Hit 12345
        # like 1 out of 10.
        #return self.cx.commands.get('random')(['%sd6' % count], True)


    def pretty(self, dice):
        display = u''
        for die in dice:
            display += '%s%s ' % (self.prettydice[int(die)-1], die)

        return display


    def getscore(self, dice):
        counter = collections.Counter(dice)
        trip = counter.most_common(1)[0]
        triple = 0
        score = 0
        scoring = 0
        scoredice = []
        min = 0
        if trip[1] > 2 and trip[0] is not None:
            triple = trip[0]
            scoring += 3
            min = 3
            scoredice = [triple,triple,triple]
            if triple == 1:
                score = 1000
            else:
                score = 100*triple
            if trip[1] > 3:
                scoredice.append(triple)
                scoring += 1
                score *= 2
            if trip[1] > 4:
                scoredice.append(triple)
                scoring += 1
                score *= 2

        for die in counter:
            if die == triple: continue
            num = counter[die]
            if die == 5:
                scoredice.extend([5] * num)
                min = 1
                scoring += num
                score += num*50
            if die == 1:
                scoredice.extend([1] * num)
                min = 1
                scoring += num
                score += num*100

        # override everything
        if sorted(dice) == [1,2,3,4,5]:
            scoring = 5
            score = 500

        return (score, scoredice, scoring, min, triple)


    def gethigh(self):
        for player in self.players:
            if self.players[player]['score'] <= self.top: continue
            self.winner = player
            self.top = self.players[player]['score']


    def checkwin(self):
        breaker = self.players[self.playerorder[self.turn]]

        if not breaker['broke']: return

        self.gethigh()
        self.chat('%s wins it with %s.' % (self.winner, self.top))

        # apply to cash
        for player in self.players:
            if player == self.winner:
                simpleupdate(player, 'cash', self.players[player]['score'], True)
            else:
                simpleupdate(player, 'cash', self.players[player]['score'] * -1, True)

        self.reset()


    def reset(self):
        self.turn = 0
        self.min = 0
        self.scoring = 0
        self.score = 0
        self.top = 0
        self.players = {}
        self.scoredice = []
        self.playerorder = []
        self.broke = False
        self.winner = None
