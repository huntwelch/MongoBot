import string
import operator

from random import choice

from autonomic import axon, alias, help, Dendrite


# Because why not. This evolved into starting
# a game, then running :guess r l s t e a o or
# whatever the most common letters are in your
# word source. Initially, we used words from
# the chat log, but they included contractions
# and shit, plus who's going to reliably guess
# dev_appserver.py, so we changed it to
# /usr/share/dict/words, but that led to the
# issue of who's going to get wokowi on their
# best day, so eventually I found a list of
# most commonly used words, which I think, but
# won't promise, is in the repository. Also,
# a full ascii hangman ended up being pretty
# spammy, so now it's a monster eating a person,
# which is probably more traumatic for children,
# even though hanging someone really should be.
# Seriously, why is this game okay?
class Hangman(Dendrite):

    word = []
    correct = []
    wrong = ''
    active = False
    monster = u'*---m^^^m\u00B0{'
    quotes = [
        'BRAAP',
        'Tastes like chicken',
        'Mmmmm... programmer',
        'Gonna regret that in the morning',
        'I should go on a diet',
        'That was gluten free, right?',
        'Still a better love story than Twilight',
    ]

    def __init__(self, cortex):
        super(Hangman, self).__init__(cortex)


    @axon
    def freqlist(self):
        try:
            auto = int(self.values[0])
            return self.frequency(auto)
        except:
            return 'Not a number'


    def frequency(self, count=False, array=False):
        letters = {}
        for line in open(self.config.wordsource):
            for _letter in line:
                letter = _letter.lower()
                if letter not in string.ascii_lowercase: continue
                if letter not in letters:
                    letters[letter] = 0
                letters[letter] += 1

        sort = sorted(letters.items(), key=operator.itemgetter(1))[::-1]

        if count:
            guesses = []
            for l,n in sort:
                guesses.append(l)
                count -= 1
                if not count:
                    break
            if array:
                return guesses
            return ' '.join(guesses)

        display = []
        for l,n in sort:
            display.append('%s (%s)' % (l, n))

        return ', '.join(display)


    @axon
    @help("<Start a game of hangman>")
    @alias('hang')
    def lizard(self):

        if self.values and self.values[0] == 'frequency':
            return self.frequency()

        if self.active: return 'Game already in progress'

        self.chat('Guess the word before the monster eats you.')

        self.active = True
        self.word = []
        self.wrong = ''
        self.correct = ''

        wordbank = []

        self.display = ' ,__oo-O'

        for line in open(self.config.wordsource):
            wordbank.append(line.strip())

        word = ''
        while len(word) > 7 or len(word) < 5:
            word = choice(wordbank)

        self.word = list(word.upper())

        self.showword()

        return self.display


    @axon
    @help("<ONE_LETTER|WHOLEWORD in an active hangman game>")
    def guess(self, internal=None):
        if not self.active:
            return 'No game in progress'

        if not self.values and not internal:
            return 'Enter "-guess one_letter|whole_word"'

        val = internal or self.values[0]

        try:
            auto = int(val)
            guesses = self.frequency(auto, True)
            for guess in guesses:
                self.guess(guess)
            return
        except:
            pass

        if len(val) == 1 and val not in string.letters:
            return "That's not a letter"

        letter = val.upper()

        if letter in self.correct or letter in self.wrong:
            return 'You already guessed that'

        if letter == ''.join(self.word):
            self.chat('"%s"' % ''.join(self.word))
            self.win()
            return
        elif len(letter) > 1:
            self.addhang()
            return

        if letter in self.word:
            self.correct += letter
            self.showword()
            return

        self.wrong += letter
        self.addhang()


    def showword(self):
        display = []
        for i in self.word:
            char = '_'
            if i in self.correct:
                char = i
            display.append(char)

        self.chat('"%s"' % ''.join(display))

        if '_' not in display:
            self.win()

    def win(self):
        self.chat('You got it!')
        self.reset()


    def lose(self):
        self.chat("You're dead. %sc--\"%s\" It was \"%s\"" % (self.monster[:-1], choice(self.quotes), ''.join(self.word)))
        self.reset()


    def reset(self):
        self.active = False
        self.word = []
        self.correct = []
        self.wrong = ''


    def addhang(self):
        self.display = self.display[1:]

        wrongness = u'%s  %s%s' % (self.wrong, self.monster, self.display)

        if len(self.display):
            self.chat(wrongness)
        else:
            self.lose()


