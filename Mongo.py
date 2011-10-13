#!/usr/local/bin/python

import sys 
import string 
import socket 
import atexit
import os

import settings,cortex
from settings import *

class Mongo:

    def __init__(self):

        self.sock = socket.socket( )
        self.sock.connect((HOST, PORT))
        self.sock.send('NICK '+NICK+'\n')
        self.sock.send('USER '+IDENT+' '+HOST+' bla :'+REALNAME+'\n')
        self.sock.send('JOIN '+CHANNEL+'\n')

        self.brain = cortex.Cortex(self)

        self.active = True
    
        while True and self.active:
            self.brain.monitor(self.sock)

    def reload(self):
        self.active = False
        self.brain.announce("strokes out.")
        reload(settings)
        from settings import *
        reload(cortex)
        self.active = True
        self.brain = cortex.Cortex(self)
        self.brain.reload()
        self.brain.announce("comes to.")

    def die(self):
        sys.exit()

connect = Mongo()
