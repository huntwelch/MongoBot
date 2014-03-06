import re

from datetime import datetime
from flask import Flask, request, session, make_response, render_template
from settings import NICK, SCAN, CHANNEL, LOG
from brainmeats.diplomacy import Countries


def diplomacy_state():
    return Countries

def render_xml(path):
    response = make_response(render_template(path))
    response.headers['Content-Type'] = 'application/xml'
    return response


def fetch_chats(request, offset):
    log = open(LOG, 'r')
    chats = []

    index = 0
    for line in log:
        # TODO: maybe move line parsing out to a general function

        timestamp = False

        # This checks for TS for back compat.
        if line[:2] == 'TS':
            clip = line.find(';')
            timestamp = line[3:clip]

            _date = datetime.fromtimestamp(float(timestamp))
            timestamp = _date.strftime('%Y-%m-%d %H:%M:%S')

            clip += 1
            line = line[clip:]



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

        private = ''

        try:

            if not bot:
                info, content = line[1:].split(' :', 1)
                sender, type, room = info.strip().split()
                nick, data = sender.split('!')
                if room != CHANNEL:
                    private = 'private'
            else:
                nick, content = line.split(': ', 1)
                nick = nick[3:]

            action = False
            if content.find('ACTION') is 1:
                content = content.replace('ACTION', '')
                action = True
        except:
            continue

        chat = {
            'time': timestamp,
            'nick': nick,
            'message': content.decode('latin-1'),
            'action': action,
            'index': index,
            'interface': 'normal',
            'private': private,
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

    # account for zero start in js

    if total <= lim:
        chats = chats
    elif offset == 0:
        chats = chats[-lim:]
    elif offset < 0:
        chats = chats[0:offset + lim]
    else:
        chats = chats[offset:offset + lim]

    return chats
