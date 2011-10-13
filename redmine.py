import sys 
import socket 
import string 
import simplejson as json
import os
import urllib2
from settings import *

class Redmine:

    def __init__(self,mongo):
        self.mongo = mongo

    def redmine(self,user,target,params=False,data=False):
        
        try:
            apikey = open(KEYS + user + ".key").read().strip()
        except:
            self.mongo.chat("No API key for user " + user)
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
            self.mongo.chat("No API key.")
 
    def showdetail(self):

        user = self.mongo.lastsender

        if not self.mongo.values:
            self.mongo.chat("Please provide a ticket number.")
            return

        ticket = self.mongo.values[0]

        self.mongo.chat("Retrieving details for ticket " + ticket + "...")
        data = self.redmine(user,"issues/" + ticket)
        self.mongo.chat("Link: " + RM_URL + "/issues/" + ticket)
        self.mongo.chat(data["description"].replace("\n",""))


    def assignment(self):

        user = self.mongo.lastsender

        if not self.mongo.values:
            self.mongo.chat("~assign ticket_number [assignee]")
            return

        ticket = self.mongo.values[0]

        if len(self.mongo.values) == 2:
            target = self.mongo.values[1]
        else:
            target = False
        
        if not target:
            target = user
            
        self.mongo.chat("Assigning ticket " + ticket + " to " + target + "...")
        put = {
            "issue":{
                "assigned_to_id":RM_USERS[target]["id"]
            }
        }        
        if self.redmine(user,"issues/" + ticket,False,put):
            self.mongo.chat("Ticket assigned")
 

    def register(self):

        sender = self.mongo.lastsender
        
        if sender not in RM_USERS:
            self.mongo.chat("You are not authorized to register.")
            return

        if not self.mongo.values:
            self.mongo.chat("Please enter a key.")
            return

        key = self.mongo.values[0]
        nkey = open(KEYS + sender + ".key",'w')
        nkey.write(components[0])
        self.mongo.chat("API key registered.") 


    def showtickets(self):

        user = self.mongo.lastsender

        if not self.mongo.values:
            whom = user
        else:
            whom = self.mongo.values[0]

        if whom not in RM_USERS:
            self.mongo.chat("User not recognized.")
            return

        self.mongo.chat("Bringing it...")
        data = self.redmine(user,"issues",{"assigned_to_id":RM_USERS[whom]["id"]})
        total = 0
        if data:
            for item in data:
                total += 1
                self.mongo.chat(RM_URL + "/issues/" 
                         + str(item['id']) 
                         + " " 
                         + item['subject'])

            if total > 0:
                self.mongo.chat(str(total) + " in all.")
            else:
                self.mongo.chat("No tickets assigned to " + whom)

 
    def showhotfix(self):

        user = self.mongo.lastsender

        self.mongo.chat("Retrieving unassigned hotfixes...")
        data = self.redmine(user,"issues",{"tracker_id":1})
        total = 0
        if data:
            for item in data:
                if not item['assigned_to_id']:
                    total += 1
                    self.mongo.chat(RM_URL + "/issues/" 
                                          + str(item['id']) 
                                          + " " 
                                          + item['subject'])

            if total > 0:
                self.mongo.chat(str(total) + " in all.")
            else:
                self.mongo.chat("No unassigned hotfixes")

 
