import sys
import socket
import string
import simplejson as json
import os
import urllib2

from autonomic import axon, category, help, Dendrite
from settings import *

# TODO: set up redmine settings and locations, make sure they're secret

@category("redmine")
class Redmine(Dendrite):
    def __init__(self, cortex):
        super(Redmine, self).__init__(cortex) 

    def redmine(self, user, target, params=False, data=False):
        try:
            apikey = open(KEYS + user + ".key").read().strip()
        except:
            self.chat("No API key for user " + user)
            return False

        cgiparams = ''
        if params:
            for item in params:
                cgiparams += "&" + item + "=" + str(params[item])

        apicall = RM_URL + "/" + target + ".json?key=" + apikey + cgiparams

        try:
            if data:
                opener = urllib2.build_opener(urllib2.HTTPHandler)
                request = urllib2.Request(apicall, data=json.dumps(data))
                request.add_header('Content-Type', 'application/json')
                request.get_method = lambda: 'PUT'
                url = opener.open(request)
                print url
                return True
            else:
                opener = urllib2.build_opener()
                response = opener.open(apicall)
                result = response.read()

                return json.loads(result)
        except:
            self.chat("No API key.")

    @axon
    @help("[ticket number] <show ticket details>")
    def showdetail(self):
        self.snag()
        user = self.lastsender

        if not self.values:
            self.chat("Please provide a ticket number.")
            return

        ticket = self.values[0]

        self.chat("Retrieving details for ticket " + ticket + "...")
        data = self.redmine(user, "issues/" + ticket)
        self.chat("Link: " + RM_URL + "/issues/" + ticket)
        self.chat(data["description"].replace("\n", ""))

    @axon
    @help("[ticket_number] [assignee] <assign a ticket to a redmine user>")
    def assignment(self):
        self.snag()

        user = self.lastsender

        if not self.values:
            self.chat("~assign ticket_number [assignee]")
            return

        ticket = self.values[0]

        if len(self.values) == 2:
            target = self.values[1]
        else:
            target = False

        if not target:
            target = user

        self.chat("Assigning ticket " + ticket + " to " + target + "...")
        put = {
            "issue": {
                "assigned_to_id": RM_USERS[target]["id"]
            }
        }
        if self.redmine(user, "issues/" + ticket, False, put):
            self.chat("Ticket assigned")

    @axon
    @help("[api key] <register your redmine api key with MongoBot>")
    def register(self):
        self.snag()

        sender = self.lastsender

        if sender not in RM_USERS:
            self.chat("You are not authorized to register.")
            return

        if not self.values:
            self.chat("Please enter a key.")
            return

        key = self.values[0]
        nkey = open(KEYS + sender + ".key", 'w')
        nkey.write(components[0])
        self.chat("API key registered.")

    @axon
    @help("[user] <show assigned tickets for user>")
    def tickets(self):
        self.snag()

        user = self.lastsender

        if not self.values:
            whom = user
        else:
            whom = self.values[0]

        if whom not in RM_USERS:
            self.chat("User not recognized.")
            return

        self.chat("Bringing it...")
        data = self.redmine(user, "issues", {"assigned_to_id": RM_USERS[whom]["id"]})
        total = 0
        if data:
            for item in data:
                total += 1
                self.chat(RM_URL + "/issues/"
                         + str(item['id'])
                         + " "
                         + item['subject'])

            if total > 0:
                self.chat(str(total) + " in all.")
            else:
                self.chat("No tickets assigned to " + whom)

    # TODO: make ticket type a variable
    @axon
    @help("<display all unassigned hotfixes>")
    def hot(self):
        self.snag() 
        
        user = self.lastsender

        self.chat("Retrieving unassigned hotfixes...")
        data = self.redmine(user, "issues", {"tracker_id": 1})
        total = 0
        if data:
            for item in data:
                if not item['assigned_to_id']:
                    total += 1
                    self.chat(RM_URL + "/issues/"
                                     + str(item['id'])
                                     + " "
                                     + item['subject'])

            if total > 0:
                self.chat(str(total) + " in all.")
            else:
                self.chat("No unassigned hotfixes")

