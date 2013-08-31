# -*- coding: utf-8 -*-

import os
import re
import subprocess

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack
from server.decorators import requires_auth
from settings import NICK, SCAN
from subprocess import PIPE

app = Flask(__name__)

# TODO: figure out how to share stuff better

@app.route("/")
def index():
    return render_template('index.html')


@app.route("/chatlogs", methods=['GET', 'POST'])
@app.route("/chatlogs/<offset>", methods=['GET'])
@requires_auth
def chatlogs(offset="0"):
    try:
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
                'msg': content.decode('latin-1'),
                'action': action, 
                'index': index, 
                'interface': 'normal', 
            }

            fader = request.args.get('fade')
            if fader and int(fader) == index:
                chat["fader"] = "fader"

            if request.method == 'POST':
                term = request.form.get('search')
                if content.find(str(term)) != -1:
                    chat["interface"] = 'search'
                    chats.append(chat)
            else:
                chats.append(chat)

            index += 1

        lim = 200
        offset = int(offset)
        total = len(chats)
        if not offset:
            offset = 0

        if total <= lim:
            chats = chats
        elif offset == 0:
            chats = chats[-lim:]
        else:
            chats = chats[offset:offset + lim]
    except Exception as e:
        chats = [e]

    try:
        return render_template('chatlogs.html', chats=chats)
    except Exception as e:
        chats = [e]
        return render_template('chatlogs.html', chats=chats)


@app.route("/callback")
@app.route("/callback.html")
def callback():
    return render_template('callback.html')

@app.route("/killbot", methods=['GET', 'POST'])
@requires_auth
def killbot():
    dead = False
    if request.method == 'POST':
        os.system('./killbot')
        subprocess.Popen('./lightning.sh', stdout=PIPE, bufsize=1)
        dead = True

    return render_template('killbot.html', nick=NICK, dead=dead)

if __name__ == "__main__":
    app.debug = True
    app.run()
