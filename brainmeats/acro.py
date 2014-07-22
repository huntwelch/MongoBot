import os

from autonomic import axon, help, Dendrite
from cybernetics import metacortex
from random import choice, randint, shuffle
from time import mktime, localtime, strftime

ACROSCORE = False

# This is probably the first official brainmeat, as we
# realized it was just to big to stuff into the cortex.
# It's also some of the oldest and least attended code,
# even after it was rewritten in the Great Brainmat
# Transition. There's at least one bug, but I haven't gotten
# to it, as it's not a deal breaker, it's just exploitable.
class Acro(Dendrite):

    active = False

    def __init__(self, cortex):
        super(Acro, self).__init__(cortex)

    @axon
    @help("[pause|resume|end] <start/pause/resume/end acro game>")
    def acro(self):
        if not self.active:
            self.run()
            return

        if not self.values:
            self.chat("Already a game in progress")
            return

        action = self.values[0]
        if action == "pause":
            if self.stage == "waiting":
                self.paused = True
                self.announce("Game paused")
            else:
                self.chat("You can only pause between rounds.")

        elif action == "resume":
            self.paused = False
            self.announce("Game on")
        elif action == "end":
            self.killgame = True
        else:
            self.chat("Not a valid action")

    @axon
    @help("<show cumulative acro game scores>")
    def boards(self):
        scores = {}

        # This is obviously a nonsense thing to do in the long term.
        for path, dirs, files in os.walk(os.path.abspath(ACROSCORE)):
            for file in files:
                for line in open(path + "/" + file):
                    if line.find(":") == -1:
                        try:
                            player, score, toss = line.split()
                            if player in scores:
                                scores[player]['score'] += int(score)
                                scores[player]['rounds'] += 1
                            else:
                                scores[player] = {'score': int(score), 'rounds': 1}
                        except:
                            continue

        for player in scores:
            score = scores[player]['score']
            average = score / scores[player]['rounds']

            self.chat(player + ": " + str(score) + " (" + str(average) + " per round)")

    @axon
    @help("<print the rules for the acro game>")
    def acrorules(self):
        self.chat("1 of 6 start game with %sacro." % self.botconf.command_prefix)
        self.chat("2 of 6 when the acronym comes up, type /msg %s your version of what the acronym stands for." % metacortex.botnick)
        self.chat("3 of 6 each word of your submission is automatically uppercased unless you preface it with '-', so 'do -it up' will show as 'Do it Up'.")
        self.chat("4 of 6 when the voting comes up, msg %s with the number of your vote." % metacortex.botnick)
        self.chat("5 of 6 play till the rounds are up.")
        self.chat("6 of 6 %s plays by default." % (metacortex.botnick))

    def gimper(self, check, action, penalty):
        gimps = []
        for player in self.players:
            if player not in check:
                gimps.append(player)

        use = self.config.insult 

        if gimps:
            trail = 0
            target = ""
            for gimp in gimps:
                post = ""
                if trail == 1:
                    use = self.config.insults
                    post = " and "
                elif trail > 1:
                    post = ", "

                if gimp in self.gimps:
                    self.gimps[gimp] += penalty
                else:
                    self.gimps[gimp] = penalty

                target = gimp + post + target
                trail += 1

            self.announce(target + " " + choice(use) +
                          " and will be docked " + str(penalty) +
                          " points for not " + action + ".")

    def endgame(self):
        self.contenders = []
        self.voters = []
        self.active = False
        self.announce("Game over.")
        self.killgame = False
        self.paused = False
        self.cx.droplive("ticker")

    def input(self, selfsub=False):
        message = self.cx.lastprivate
        if message == self.matchlast:
            return

        self.matchlast = message

        if self.paused:
            self.chat("Game is paused.")
            return

        if not selfsub:
            sender = message[0][1:].split('!')[0]
            entry = message[3][1:]
        else:
            sender = metacortex.botnick
            entry = self.cx.brainmeants["broca"].acronymit(self.currentacronym)

        if sender not in self.players and self.round != 1:
            return

        if self.stage == "submit":

            entries = 0

            for line in open(self.record):
                try:
                    current, subber, timed, what = line.split(":", 3)
                except:
                    continue

                if int(current) == self.round:
                    entries += 1
                if int(current) == self.round and sender == subber:
                    return

            if not selfsub:
                _time = int(mktime(localtime()) - self.mark)
            else:
                _time = int(self.config.roundtime / 2)

            words = entry.split()
            temp = []
            for word in words:
                if word[:1] == "-":
                    temp.append(word[1:])
                else:
                    temp.append(word.capitalize())
                    open(self.cx.settings.directory.storage + "/natwords", 'a').write(word.capitalize() + "\n")

            entry = ' '.join(temp)

            er = str(self.round) + ":" + sender + ":" + str(_time) + ":" + entry + "\n"
            open(self.record, 'a').write(er)
            numplayers = len(self.players)
            received = entries + 1

            addition = ""
            if self.round != 1:
                addition = str(numplayers - received) + " more to go."

            if not selfsub:
                self.announce("Entry recieved at " + str(_time) + " seconds. " + addition)

            if received == numplayers and self.round != 1:
                self.bypass = True
            elif self.round == 1:
                self.players.append(sender)

        elif self.stage == "voting":
            if self.config.botplay and metacortex.botnick not in self.voters:
                self.voters.append(metacortex.botnick)

            if len(self.players) < self.config.minplayers:
                self.announce("Need at least" + str(self.config.minplayers) + " players. Sorry.")

            try:
                vote = int(entry)
            except:
                return

            if sender == self.contenders[vote - 1]["player"]:
                self.announce(sender + " tried to vote for himself. What a bitch.")
                return

            try:
                self.contenders[vote - 1]["votes"] += 1
                self.voters.append(sender)
                if len(self.voters) == len(self.players):
                    self.bypass = True
            except:
                return

    def setup(self):
        self.record = ACROSCORE + strftime('%Y-%m-%d-%H%M') + '.game'
        open(self.record, "w")

        self.active = True

        self.cumulative = {}
        self.start = mktime(localtime())
        self.mark = mktime(localtime())
        self.round = 1

        self.stage = "waiting"

        self.matchlast = False
        self.killgame = False
        self.warned = False
        self.bypass = False
        self.displayed = False

        self.voters = []
        self.players = []
        self.gimps = {}
        self.selfsubbed = False
        self.paused = False
        self.killgame = False

    def run(self):
        self.setup()
        self.announce("New game commencing in " + str(self.config.rest) + " seconds")
        self.cx.addlive(self.ticker)

    def ticker(self):

        if self.killgame:
            self.endgame()
            return

        if self.paused:
            return

        self.input()

        self.current = mktime(localtime())

        {
            "waiting": self.waiting,
            "submit": self.submit,
            "voting": self.voting,
        }.get(self.stage)()

    def waiting(self):
        if self.current <= self.mark + self.config.rest:
            return

        letters = []
        for line in open(self.cx.settings.directory.storage + "/letters"):
            addition = line.split()
            addition.pop()
            letters.extend(addition)

        acronym = ""
        length = randint(self.config.minlen, self.config.maxlen)
        for i in range(1, length):
            acronym = acronym + choice(letters).upper()

        self.currentacronym = acronym
        self.mark = mktime(localtime())
        self.announce("Round " + str(self.round) +
                      " commencing! Acronym is " + acronym)

        self.stage = "submit"

    def submit(self):
        if self.current > self.mark + self.config.roundtime - self.config.warning and not self.warned:
            self.warned = True
            self.announce(str(self.config.warning) + " seconds left...")
            return

        if self.config.botplay and not self.selfsubbed:
            self.input(True)
            self.selfsubbed = True

        if self.current <= self.mark + self.config.roundtime and not self.bypass:
            return

        if self.round == 1:
            for player in self.players:
                self.cumulative[player] = 0

        self.bypass = False
        self.warned = False
        self.announce("Round over, sluts. Here are the contenders:")

        self.contenders = []
        submitters = []
        for line in open(self.record):
            try:
                r, s, t, c = line.split(":", 3)
            except:
                continue

            if int(r) == self.round:
                submitters.append(s)
                self.contenders.append({
                    "player": s,
                    "time": t,
                    "entry": c.strip(),
                    "votes": 0,
                })

        shuffle(self.contenders)
        item = 1
        for submission in self.contenders:
            self.announce(str(item) + ": " + submission["entry"])
            item += 1

        if not self.contenders:
            self.announce("Don't waste my friggin time")
            # sys.exit()

        if self.round != 1:
            self.gimper(submitters, "submitting", self.config.noacropenalty)

        self.announce("You have " + str(self.config.votetime) + " seconds to vote.")
        self.mark = mktime(localtime())
        self.stage = "voting"

    def voting(self):
        if self.current <= self.mark + self.config.votetime and not self.bypass:
            return

        self.bypass = False
        self.announce("Votes are in. The results:")

        for r in self.contenders:
            if r['votes'] == 0:
                note = "dick."
            elif r['votes'] == 1:
                note = "1 vote."
            else:
                note = str(r['votes']) + " votes."

            self.announce(r['player'] + "'s \"" + r['entry'] + "\" got " + note)

        self.gimper(self.voters, "voting", self.config.novotepenalty)

        results = {}
        for player in self.players:
            results[player] = {"score": 0,
                               "votes": 0,
                               "timebonus": 0}

            if player in self.gimps:
                results[player]["score"] -= self.gimps[player]

        for r in self.contenders:
            if r['votes'] != 0:
                results[r['player']]['score'] += r['votes'] * 10
                results[r['player']]['votes'] = r['votes']
                if int(r['time']) < self.config.roundtime / 2:
                    timebonus = int((self.config.roundtime / 2 - int(r['time'])) / self.config.timefactor)
                else:
                    timebonus = 0

                results[r['player']]['timebonus'] = timebonus
                results[r['player']]['score'] += timebonus

        tally = "Round:" + str(self.round) + "\n"

        for result in results:
            sc = results[result]

            self.cumulative[result] += sc['score']

            score = str(sc['score'])
            bonus = str(sc['timebonus'])
            total = str(self.cumulative[result])

            self.announce(result + " came in with " + score +
                          " with a time bonus of " + bonus +
                          ", for a total of " + total)

            tally += result + " " + str(sc['score']) + " (" + str(sc['timebonus']) + ")\n"

        open(self.record, 'a').write("\n" + tally + "\n")

        # Record in game tally

        if self.round == self.config.rounds:
            self.killgame = True
            return

        self.selfsubbed = False
        self.voters = []
        self.contenders = []
        self.gimps = {}
        self.mark = mktime(localtime())
        self.announce("Next round in " + str(self.config.rest) + " seconds.")
        self.round += 1
        self.stage = "waiting"
