import imaplib
import email
import smtplib

from autonomic import axon, alias, help, Dendrite, Cerebellum, Synapse, Receptor

@Cerebellum
class Mail(Dendrite):

    logged = []
    imap = False
    smtp = False

    def __init__(self, cortex):
        super(Mail, self).__init__(cortex)

        self.imap = imaplib.IMAP4_SSL(self.config.imap)
        self.imap.login(self.secrets.user, self.secrets.password)


    # Example command function
    # The axon decorator adds it to the available chatroom commands,
    # based on the name of the function. The @help adds an entry to
    # the appropriate category.
    @axon
    @help("<I am an example>")
    def function_name(self):
        return


    @axon
    def fetch(self):
        self.imap.select('inbox')
        result, data = self.imap.uid('search', None, "UnSeen") # search and return uids instead
        print data
        new = 0
        for mail in data[0].split():
            uid = mail.split()[-1]

            if uid in self.logged: continue

            self.logged.append(uid)
            new += 1    
            
        if not new: return

        self.chat('You have %s unread emails' % new)

        return
