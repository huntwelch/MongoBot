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
            file = open(STORAGE + "/introductions")
        except:
            self.chat("No introductions file")
            return

        for line in file:
            if line.strip() == "---":
                self.chat(text)
                text = ""
                continue

            text += " " + line.strip()

        self.chat(text)

    @axon
    @help("<save your current copmany>")
    def workat(self):
        self.snag()
        if not self.values: 
            self.chat("If you're unemployed, that's cool, just don't abuse the bot")
            return
        
        name = self.lastsender  
        company = " ".join(self.values)

        drinker = Drinker.objects(name = name)
        if drinker:
            drinker = drinker[0]
            drinker.company = company
        else:
            drinker = Drinker(name = name, company = company) 

        drinker.save()

    @axon
    @help("<show where everyone works>")
    def companies(self):
        self.snag()
        for drinker in Drinker.objects:
            self.chat(drinker.name + ": " + drinker.company)

    @axon
    @help("<[person] show where person works>")
    def company(self):
        self.snag()
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        user = Drinker.objects(name = search_for)[0]
        if user and user.company:
            self.chat(user.name + ": " + user.company)
        else:
            self.chat("Tell that deadbeat %s to get a damn job already..." % search_for)

    @axon
    @help("<ping everyone in the room>")
    def all(self):
        self.snag()
        peeps = self.members
        try:
            peeps.remove(self.lastsender)
        except:
            self.chat('List incoherrent')
            return

        peeps = ', '.join(peeps)
        self.chat(peeps + ', ' + self.lastsender + ' has something very important to say.')


