#!/usr/local/bin/python

import sys 
import string 
import socket 
import atexit
import os

import acro,settings,cortex
from acro import Acro
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
        self.brain.act("strokes out.")
        reload(settings)
        from settings import *
        reload(cortex)
        reload(acro)
        from acro import Acro
        self.active = True
        self.brain = cortex.Cortex(self)
        self.brain.act("comes to.")

    def die(self):
        sys.exit()

connect = Mongo()
