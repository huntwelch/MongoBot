import sys


class Spoon:
    def __init__(self, inputword):
        self.inputword = inputword
        self.inputwordsplit = self.splitter(inputword)
        with open('/usr/share/dict/words') as fp:
            self.words = set(line.strip() for line in fp.readlines() if line.islower() and len(line.strip()) > 3)

        spoons = [self.spoonit(w) for w in self.words]
        self.view = [x for x in spoons if x]


    def show(self):
        return self.view


    def splitter(self, word):
        if word[:2] == 'qu': return 2
        vowelpos = [char in "aeiouy" for char in word].index(True)
        if not vowelpos:
            if not any(char in "aeiouy" for char in word[1:]): return 0
            vowelpos = [char in "aeiouy" for char in word[1:]].index(True)

        return vowelpos


    def generate(self, word):
        if not any(char in "aeiou" for char in word): return []

        wordsplit = self.splitter(word)
        if not wordsplit: return []

        if word[wordsplit:] == self.inputword[self.inputwordsplit:]: return []
        if word[:wordsplit] == self.inputword[:self.inputwordsplit]: return []

        spoon_1 = word[:wordsplit] + self.inputword[self.inputwordsplit:]
        spoon_2 = self.inputword[:self.inputwordsplit] + word[wordsplit:]

        return [spoon_1, spoon_2]


    def spoonit(self, word):
        spoonset = self.generate(word)

        if not spoonset: return False
        if spoonset[0] not in self.words: return False
        if spoonset[1] not in self.words: return False

        return spoonset[0] + ' ' + spoonset[1]

