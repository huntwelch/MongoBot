import socket
import os

from multiprocessing import Process
from config import load_config

class Cellphone(object):
    settings = False
    secrets = False
    address = '/tmp/intercom.sock'
    radio = None
    phone = None

    # Initialize and auto-connect
    def __init__(self, master, cortex):

        self.cx = cortex
        self.master = master

        self.settings = load_config('config/settings.yaml')
        self.secrets = load_config('config/secrets.yaml')

        if master.radio:
            self.radio = master.radio

    def accept(self):
        self.radio.listen(5)
        self.phone, _ = self.radio.accept()

    def connect(self):
        try:
            os.remove(self.address)
        except:
            pass
        self.radio = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.radio.bind(self.address)
        self.master.radio = self.radio

        p = Process(target=self.accept)
        p.start()


    # Read data in from the socket
    def read(self):
        try:
            data = self.phone.recv(1024)
        except Exception as e:
            return

        if data == b'':
            print 'Can you hear me now?'
            sys.exit()

        return data

    # Send data out to the bound socket
    def send(self, data):
        self.phone.send(data)

    # Process incoming data
    def process(self):
        data = self.read()

        if not data:
            return

        args = data.split()

        try:
            self.command(args)
        except Exception as e:
            return

    def command(self, args):
        command = args.pop(0)
        # Only expose public commands
        if command not in self.cx.public_commands:
            self.send('My daddy says not to listen to you.')

        if not command:
            return

        if args:
            self.cx.values = arguments
        else:
            self.cx.values = False

        self.send(self.cx.commands.get(command))
