from random import choice

from autonomic import axon, alias, help, Dendrite
from settings import STORAGE, ACROLIB


# Because why not
class Hangman(Dendrite):

    word = []
    correct = []
    wrong = ''
    active = False

    states = [
        {'2': '|    O    '},
        {'3': '|    |    ', '4': '|    |    '},
        {'5':'|   /     '},
        {'5':'|   / \   '},
        {'3': '|  --|    '},
        {'3': '|  --|--  '},
    ]


    def __init__(self, cortex):
        super(Hangman, self).__init__(cortex)

    # Example command function
    # The axon decorator adds it to the available chatroom commands,
    # based on the name of the function. The @help adds an entry to 
    # the appropriate category.
    @axon
    @help("<Start a game of hangman>")
    def hang(self):
        
        if self.active: return 'Game already in progress'

        self.active = True
        self.word = []
        self.correct = []
        self.wrong = ''

        wordbank = []

        self.display = [
            '|-----    ',
            '|    |    ',
            '|         ',
            '|         ',
            '|         ',
            '|         ',
            '|         ',
            '|_________',
            '',
        ]

        for line in open("%s/%s" % (STORAGE, ACROLIB)):
            wordbank.append(line.strip())

        word = ''
        while len(word) > 7 or len(word) < 5:
            word = choice(wordbank)

        self.word = list(word.upper())

        self.showword()

        return self.display

    @axon
    def guess(self):
        if not self.active:
            return 'No game in progress'

        if not self.values:
            return 'Enter "-guess one_letter|whole_word"'
        
        if self.values[0].upper() == ''.join(self.word):
            self.chat('"%s"' % display)
            self.win()
        
        _g = self.values[0][:1].upper()

        if _g in self.word:
            correct = [ i for i,l in enumerate(self.word) if l == _g ]
            self.correct += correct
            self.showword()
            return

        self.wrong += _g
        self.addhang()

        return self.display

    def showword(self):
        
        display = []
        for i in range(0, len(self.word)):
            char = '_'
            if i in self.correct:
                char = self.word[i]
            display.append(char)

        self.chat('"%s"' % ''.join(display))

        if '_' not in display:
            self.win()

    def win(self):
        self.chat('You got it!')
        self.reset()


    def lose(self):
        self.chat("You're dead. It was \"%s\"" % ''.join(self.word))
        self.reset()


    def reset(self):
        self.active = False
        self.word = []
        self.correct = []
        self.wrong = ''


    def addhang(self):
        numwrong = len(self.wrong)
        for i in range(0, numwrong):
            alt = self.states[i]
            for state in alt:
                self.display[int(state)] = alt[state]
        
        self.chat(self.wrong)

        if len(self.wrong) == len(self.states):
            self.lose()

