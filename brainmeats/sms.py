import re

from autonomic import axon, help, Dendrite, Cerebellum, Receptor
from time import mktime, localtime
from twilio.rest import TwilioRestClient
from datastore import Drinker
from config import load_config
from id import Id
import traceback

# This shit be awesome. It requires a twilio account, but
# there's no better way to hive-mind-fuck with someone.
@Cerebellum
class Sms(Dendrite):

    client = False
    incoming = []
    loaded = False
    current = mktime(localtime())
    next_ = current + 10

    def __init__(self, cortex):
        super(Sms, self).__init__(cortex)

        self.client = TwilioRestClient(self.secrets.sid, self.secrets.token)


    # smsticker is a receptor that responds to twitch 
    # broadcasts - which happen on every iteration of
    # monitor. to prevent hitting twilio too hard, 
    # this gets self limited to every 10 seconds.
    @Receptor('twitch')
    def smsticker(self):

        self.current = mktime(localtime())

        # Only check every 10 seconds
        if self.current < self.next_:
            return

        self.next_ += 10

        try:
            messages = self.client.sms.messages.list(to=self.secrets.number)
        except:
            print "Error fetching"
            return

        while messages:
            item = messages.pop()
            sid = item.sid

            if sid in self.incoming:
                continue

            self.incoming.append(sid)

            # Don't parse previously received messages until the 
            # incoming list has been fully parsed
            if not self.loaded:
                continue

            clipped = item.from_[2:]
            drinker = Id(phone=clipped)
            
            # Note that this trusts the phone number, on the grounds
            # there must have been access to the system to get the
            # number in there. Normal ident auths can't be applied.
            if drinker:
                from_ = drinker.name
            else:
                from_ = item.from_

            # TODO: Make this determine the default channel!!
            self.cx.context = '#okdrink'

            message = 'SMS from %s: %s' % (from_, item.body)

            self.announce(message)

            # Check if the incoming message contained a command
            match = re.search('^\{0}(\w+)[ ]?(.+)?'.format(self.cx.settings.bot.command_prefix), item.body)
            if match and drinker:

                command = match.group(1)
                arguments = match.group(2)

                try:
                    resp = self.cx.command(drinker.name, item.body, silent=True)

                    message = self.client.messages.create(
                        body=resp,
                        to=drinker.phone,
                        from_=self.secrets.number
                    )

                    self.chat('Message sent: ' + message.sid)
                except Exception as e:
                    self.chat(str(e))


        self.loaded = True


    @axon
    @help('NUMBER|USERNAME MESSAGE <send an sms message to unsuspecting victim>')
    def sms(self):

        if self.context not in self.cx.channels:
            self.chat('No private sms abuse. Tsk tsk.')
            return

        if not self.values:
            self.chat('-sms <number> <message>')
            return

        to = self.values[0]
        msg = ' '.join(self.values[1:])

        if not re.search('^[+0-9]+$', to):
            user = Id(to)
            if not user or not user.phone:
                self.chat('Don\'t know who that is :(')
                return
            else:
                to = user.phone

        try:
            params = {
                'to': to,
                'from_': self.secrets.number
            }

            regex = '^http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+$'
            match = re.search(regex, msg)
            if match:
                params['media_url'] = msg
            else:
                params['body'] = msg

            message = self.client.messages.create(**params)
            self.chat('Message sent: ' + message.sid)
        except Exception as e:
            self.chat(str(e))

        return


    @axon
    @help('[FROM NUMBER] <check for sms replies to messages previously sent to unsuspecting victims>')
    def smsmsgs(self):
        if not self.values:
            self.chat('What number?')
            return

        num = self.values[0]

        try:
            messages = self.client.messages.list(to=self.secrets.number, from_=num)
            for item in messages:
                self.chat(item.from_ + ': ' + item.body)
        except:
            self.chat('Done broke')
            return
