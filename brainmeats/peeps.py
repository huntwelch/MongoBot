import datetime

from autonomic import axon, category, help, Dendrite
from settings import STORAGE, CHANNEL
from datastore import Drinker


@category("peeps")
class Peeps(Dendrite):
    def __init__(self, cortex):
        super(Peeps, self).__init__(cortex)

    @axon
    @help("<show history of " + CHANNEL + ">")
    def history(self):
        text = ""
        try:
            with open(STORAGE + "/introductions") as file:
                for line in file:
                    if line.strip() == "---":
                        self.chat(text)
                        text = ""
                        continue

                    text += " " + line.strip()
        except:
            self.chat("No introductions file")
            return

        self.chat(text)

    @axon
    @help("COMPANY <save your current copmany>")
    def workat(self):
        if not self.values:
            self.chat("If you're unemployed, that's cool, just don't abuse the bot")
            return

        name = self.lastsender
        company = " ".join(self.values)

        drinker = Drinker.objects(name=name)
        if drinker:
            drinker = drinker[0]
            drinker.company = company
        else:
            drinker = Drinker(name=name, company=company)

        drinker.save()

    @axon
    @help("<show where everyone works>")
    def companies(self):
        for drinker in Drinker.objects:
            self.chat("%s: %s" % (drinker.name, drinker.company))

    @axon
    @help("USERNAME <show where person works>")
    def company(self):
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        user = Drinker.objects(name=search_for).first()
        if user and user.company:
            self.chat(user.name + ": " + user.company)
        else:
            self.chat("Tell that deadbeat %s to get a damn job already..." % search_for)

    @axon
    @help("<ping everyone in the room>")
    def all(self):
        peeps = self.members
        try:
            peeps.remove(self.lastsender)
        except:
            self.chat('List incoherrent')
            return

        peeps = ', '.join(peeps)
        self.chat(peeps + ', ' + self.lastsender + ' has something very important to say.')

    @axon
    def awaiting(self):
        if not self.values:
            self.chat("Whatchu waitin fo?")
            return
        
        name = self.lastsender
        awaits = " ".join(self.values)

        drinker = Drinker.objects(name=name)
        if drinker:
            drinker = drinker[0]
            drinker.awaiting = awaits
        else:
            drinker = Drinker(name=name, awaiting=awaiting)

        drinker.save()
        self.chat("Antici..... pating.")
       

    @axon
    def timeleft(self):
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        drinker = Drinker.objects(name=search_for).first()
        if not drinker or not drinker.awaiting:
            self.chat("%s waits for nothing." % search_for)
            return

        try:
            moment, event = drinker.awaiting.split("=") 
            year, month, day = moment.split("/")
            delta = datetime.date(int(year), int(month), int(day)) - datetime.date.today()

            self.chat("Only %s days till %s" % (delta.days, event))
        except:
            self.chat("Couldn't parse that out.")
