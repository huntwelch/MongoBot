import sys
import socket
import string
import simplejson as json
import os
import urllib2

from autonomic import axon, category, help, Dendrite
from settings import KEYS, RM_USERS, RM_URL

# TODO: set up redmine settings and locations, make sure they're secret


@category("organize")
class Organize(Dendrite):
    def __init__(self, cortex):
        super(Organize, self).__init__(cortex)

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
            self.chat("No data found.")

    @axon
    @help("TICKET_NUMBER <show ticket details>")
    def showdetail(self):
        user = self.lastsender

        if not self.values:
            self.chat("Please provide a ticket number.")
            return

        ticket = self.values[0]

        try:
            self.chat("Retrieving details for ticket " + ticket + "...")
            data = self.redmine(user, "issues/" + ticket)
            self.chat("Link: " + RM_URL + "/issues/" + ticket)
            self.chat(data["description"].replace("\n", ""))
        except:
            self.chat("Failed to access Redmine.")

    @axon
    @help("TICKET_NUMBER [ASSIGNEE] <assign a ticket to yourself or a redmine user>")
    def assign(self):
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
    @help("API_KEY <register your redmine api key with " + NICK + ">")
    def register(self):
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
    @help("[USER] <show assigned tickets for self or redmine user>")
    def tickets(self):
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

    @axon
    @help("TRACKER_ID <display all unassigned tickets of a certain type>")
    def hot(self):
        user = self.lastsender

        if not self.values:
            self.chat("No id.")
            return

        self.chat("Retrieving unassigned tickets...")
        data = self.redmine(user, "issues", {"tracker_id": self.values[0]})
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
                self.chat("No unassigned tickets of that type")
