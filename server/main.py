# -*- coding: utf-8 -*-

import os
import re
import subprocess
import simplejson as json 

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack
from server.decorators import requires_auth
from settings import NICK, SCAN
from subprocess import PIPE

app = Flask(__name__)

# TODO: rethink offsets for start of file

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/api/chat", methods=['GET', 'POST'])
def api_chat():
    offset = False
    if request.args.get('offset'):
        offset = request.args.get('offset')
    chats = fetchchats(request, offset)
    return json.dumps(chats)

@app.route("/chatlogs")
@requires_auth
def chatlogs():
    hint = 'Press "/" to search logs.'
    return render_template('chatlogs.html', hint=hint)
    
def fetchchats(request, offset):
    log = open('hippocampus/log/chat.log', 'r')
    chats = []

    index = 0
    for line in log:

        # TODO: maybe move line parsing out to a general function
        if line.find(NICK) is 1:
            continue

        bot = False
        if line.find('___' + NICK) is 0:
            bot = True

        if line.find('PRIVMSG') == -1 and not bot:
            continue
        if not re.search("^:", line) and not bot:
            continue

        if re.search(SCAN, line) and not bot:
            continue

        if not bot:
            info, content = line[1:].split(' :', 1)
            sender, type, room = info.strip().split()
            nick, data = sender.split('!')
        else:
            nick, content = line.split(': ', 1)
            nick = nick[3:]

        action = False
        if content.find('ACTION') is 1:
            content = content.replace('ACTION', '')
            action = True

        chat = {
            'nick': nick, 
            'message': content.decode('latin-1'),
            'action': action, 
            'index': index, 
            'interface': 'normal', 
        }

        fader = request.args.get('fade')
        if fader and int(fader) == index:
            chat["fader"] = "fader"

        if request.args.get('search'):
            term = request.args.get('search')
            if content.find(str(term)) != -1:
                chat["interface"] = 'search'
                chats.append(chat)
        else:
            chats.append(chat)

        index += 1

    lim = 100
    offset = int(offset)
    total = len(chats)

    if total <= lim:
        chats = chats
    elif offset == 0:
        chats = chats[-lim:]
    else:
        chats = chats[offset:offset + lim]

    return chats


@app.route("/callback")
@app.route("/callback.html")
def callback():
    return render_template('callback.html')

if __name__ == "__main__":
    app.debug = True
    app.run()
