import datetime
import re
import hashlib

from autonomic import axon, category, help, Dendrite, alias
from settings import STORAGE, CHANNEL
from secrets import USERS
from datastore import simpleupdate, Drinker, incrementEntity, Entity, entityScore


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

        if not simpleupdate(name, "company", company):
            self.chat("Busto, bro.")
            return

        self.chat("Company updated.")

    @axon
    @help("DRINKER <give somebody a point>")
    def increment(self):
        if not self.values:
            self.chat("you need to give someone your love")
            return
        entity = " ".join(self.values)

        if not incrementEntity(entity, 1):
            self.chat("mongodb seems borked")
            return
        self.chat(self.lastsender + " brought " + entity + " to " + str(entityScore(entity)))

    @axon
    @help("DRINKER <take a point away>")
    def decrement(self):
        if not self.values:
            self.chat("you need to give someone your hate")
            return
        entity = " ".join(self.values)

        if not incrementEntity(entity, -1):
            self.chat("mongodb seems borked")
            return
        self.chat(self.lastsender + " brought " + entity + " to " + str(entityScore(entity)))

    @axon
    @help("<show where everyone works>")
    def companies(self):
        for drinker in Drinker.objects:
            if "_" not in drinker.name:
                self.chat("%s: %s" % (drinker.name, drinker.company))

    @axon
    @help("[USERNAME] <show where you or USERNAME works>")
    def company(self):
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        user = Drinker.objects(name=search_for).first()
        if not user or not user.company:
            self.chat("Tell that deadbeat %s to get a damn job already..." % search_for)
        else:
            self.chat(user.name + ": " + user.company)

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
    @help("YYYY/MM/DD=EVENT_DESCRIPTION <save what you're waiting for>")
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
    @help("[USERNAME] <show what you are or USERNAME is waiting for>")
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

    @axon
    @help("USERNAME <give temporary access to USERNAME>")
    def guestpass(self):
        if not self.values or not re.match("^[\w_]+$", self.values[0]):
            self.chat("Invalid entry.")
            return
        else:
            guest = self.values[0]

        USERS.append(guest)

        self.chat("Hi " + guest + ". You seem okay.")

    @axon
    @help("PASSWORD <set admin password>")
    def passwd(self):
        if not self.values:
            self.chat("Enter a password.")
            return

        if self.context == CHANNEL:
            self.chat("Not in the main channel, you twit.")
            return

        whom = self.lastsender

        h = hashlib.sha1()
        h.update(' '.join(self.values))
        pwd = h.hexdigest()

        if not simpleupdate(whom, "password", pwd):
            self.chat("Fail.")
            return

        self.chat("Password set.")

    @axon
    @help("PHONE_NUMBER <add your phone number to your profile for sms access>")
    def addphone(self):
        if not self.values:
            self.chat("What number?")
            return

        phone = self.values[0]

        if not re.search("^[0-9]{10}$", phone):
            self.chat("Just one good ol'merican ten-digit number, thank ya kindly.")
            return

        name = self.lastsender

        if not simpleupdate(name, "phone", phone):
            self.chat("Some shit borked.")
            return

        self.chat("Number updated.")

    @axon
    @help("[USERNAME] <view your own phone number or another drinker's>")
    def digits(self):
        if not self.values:
            search_for = self.lastsender
        else:
            search_for = self.values[0]

        user = Drinker.objects(name=search_for).first()
        if not user or not user.phone:
            self.chat("No such numba. No such zone.")
        else:
            self.chat(user.name + ': ' + user.phone)
