import imaplib
import email
import smtplib

from autonomic import axon, alias, help, Dendrite, Cerebellum, Synapse, Receptor
from email.mime.text import MIMEText

# Lot of potential here. Currently just making
# it a kind of daily wrap up thingy.
@Cerebellum
class Mail(Dendrite):

    logged = []
    imap = False
    smtp = False

    def __init__(self, cortex):
        super(Mail, self).__init__(cortex)

        self.imap = imaplib.IMAP4_SSL(self.config.imap)
        self.imap.login(self.secrets.user, self.secrets.password)

        self.smtp = smtplib.SMTP(self.config.smtp)
        self.smtp.starttls()
        self.smtp.login(self.secrets.user, self.secrets.password)


    @axon
    @help('Check for new mail')
    def fetch(self):
        unread = self.getnew()
        if not unread:
            return 'Fail.'

        return 'You have %s unread emails' % len(unread)


    def getnew(self):
        try:
            self.imap.select('inbox')
            result, data = self.imap.uid('search', None, "UnSeen") # search and return uids instead
        except:
            return False

        new = []
        for mail in data[0].split():
            uid = mail.split()[-1]

            if uid in self.logged: continue

            self.logged.append(uid)
            new.append(uid)
            
        if not new: return False

        return new


    def rollup(self, sender, subjects):

        name, address = sender
        subs = subjects.split()

        stuff = []

        # This construction is just to ensure babble
        # outputs, as it occasionally returns nothing
        babble = False
        while not babble:
            babble = self.cx.commands.get('babble', self.cx.default)()
        babble = 'Inspiration: %s' % babble
        stuff.append(babble)

        if len(subs) == 2:
            self.cx.values = [subs[1]]
            weather = self.cx.commands.get('weather', self.cx.default)() 
            stuff.append(weather)

        msg = MIMEText('\n\n'.join(stuff))
        msg['Subject'] = 'Stuff fetched'

        try:
            self.smtp.sendmail(self.secrets.email, sender, msg.as_string())
        except Exception as e:
            print str(e)

        return


    @Receptor('twitch')
    def responder(self):
        
        incoming = self.getnew() 

        if not incoming: return

        for mailid in incoming:
            try:
                result, data = self.imap.uid('fetch', mailid, '(RFC822)')
            except:
                continue

            raw = data[0][1]
            message = email.message_from_string(raw)
            
            if 'rollup' not in message['Subject']: continue

            try:
                self.imap.uid('store', mailid, '+FLAGS', r'(\Deleted)') 
                self.imap.expunge()
            except Exception as e:
                print str(e)

            sender = email.utils.parseaddr(message['From'])
            self.rollup(sender, message['Subject'])

        return
