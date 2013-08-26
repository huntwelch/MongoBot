import re

from autonomic import axon, alias, category, help, Dendrite
from time import mktime, localtime, strftime
from secrets import TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, SAFE_NUMBERS
from settings import CONTROL_KEY, CHANNEL
from twilio.rest import TwilioRestClient
from secrets import USERS
from datastore import Drinker

@category("sms")
class Sms(Dendrite):
    def __init__(self, cortex):
        super(Sms, self).__init__(cortex)
        self.client = TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)
        self.incoming = []
        self.loaded = False
        self.current = mktime(localtime())
        self.next_ = self.current + 10
        self.cx.addlive(self.smsticker)

        return

    def smsticker(self):

        self.current = mktime(localtime())

        if self.current < self.next_:
            return

        self.next_ += 10

        try:
            messages = self.client.sms.messages.list(to="+16468635380")
        except:
            print "Error fetching" 
            print messages
            return

        while messages:
            item = messages.pop()
            sid = item.sid

            if sid in self.incoming:
                continue

            self.incoming.append(sid)

            if not self.loaded:
                continue

            clipped = item.from_[2:]
            drinker = Drinker.objects(phone=clipped)

            if drinker:
                from_ = drinker[0].name
            else:
                from_ = item.from_

            message = "SMS from " + from_ + ": " + item.body

            self.announce(message) 

            if item.body[:1] == CONTROL_KEY and drinker:
                self.cx.context = CHANNEL 
                self.cx.command(drinker[0].name, item.body) 
                
        self.loaded = True

    @axon
    @help("NUMBER|USERNAME MESSAGE <send an sms message to unsuspecting victim>")
    def sms(self):
        if self.context != CHANNEL:
            self.chat("No private sms abuse. Tsk tsk.")
            return

        if not self.values:
            self.chat("-sms <number> <message>")
            return

        to = self.values[0]
        msg = " ".join(self.values[1:])

        if not re.search("^[+0-9]+$", to):
            user = Drinker.objects(name=to).first()
            if not user or not user.phone:
                self.chat('No num found')
                return
            else:
                to = user.phone

        try:
            message = self.client.sms.messages.create(
                body=msg,
                to=to,
                from_=TWILIO_NUMBER
            )
            self.chat("Message sent: " + message.sid)
        except:
            self.chat("Done broke")
            return

    @axon
    @help("[FROM NUMBER] <check for sms replies to messages previously sent to unsuspecting victims>")
    def smsmsgs(self):
        if not self.values:
            self.chat("What number?")
            return

        num = self.values[0]

        try:
            messages = self.client.sms.messages.list(to="+16468635380",from_=num)
            for item in messages:
                self.chat(item.from_ + ": " + item.body)
        except:
            self.chat("Done broke")
            return

