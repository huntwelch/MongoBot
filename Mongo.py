#!/usr/bin/env python

import sys
import string
import socket
import atexit
import os

import settings
import cortex
from settings import *


class Mongo:

    def __init__(self):

        self.sock = socket.socket()
        self.sock.connect((HOST, PORT))
        self.sock.send('NICK ' + NICK + '\n')
        self.sock.send('USER ' + IDENT + ' ' + HOST + ' bla :' + REALNAME + '\n')
        self.sock.send('JOIN ' + CHANNEL + '\n')

        self.brain = cortex.Cortex(self)

        self.active = True

        while True and self.active:
            self.brain.monitor(self.sock)

    def reload(self):

        quiet = False
        if not self.brain.values or not len(self.brain.values[0]):
            self.brain.act("strokes out.")
        else:
            quiet = True
            self.brain.act("strokes out.", False, OWNER)

        self.active = False
        reload(settings)
        from settings import *
        reload(cortex)
        self.active = True
        self.brain = cortex.Cortex(self)
        self.brain.reload()

        if not quiet:
            self.brain.act("comes to.")
        else:
            self.brain.act("comes to.", False, OWNER)

    def die(self):
        sys.exit()

connect = Mongo()
