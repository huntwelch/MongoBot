import string

from random import choice

from autonomic import axon, alias, help, Dendrite


# Because why not
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
    @help("<Start a game of hangman>")
    @alias('hang')
    def lizard(self):
        
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
    def guess(self):
        if not self.active:
            return 'No game in progress'

        if not self.values:
            return 'Enter "-guess one_letter|whole_word"'
        
        if len(self.values[0]) == 1 and self.values[0] not in string.letters:
            return "That's not a letter"

        letter = self.values[0].upper()

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


