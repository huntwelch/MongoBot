# -*- coding: utf-8 -*-

import simplejson as json 

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack
from server.decorators import requires_auth
from server.helpers import fetch_chats, render_xml


app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')


@app.route("/api/chat", methods=['GET', 'POST'])
def api_chat():
    offset = False
    if request.args.get('offset'):
        offset = request.args.get('offset')
    chats = fetch_chats(request, offset)
    return json.dumps(chats)


@app.route("/chatlogs")
@requires_auth
def chatlogs():
    hint = 'Press "/" to search logs.'
    return render_template('chatlogs.html', hint=hint)


@app.route("/voice.xml")
def twilio_voice():
    return render_xml('voice.xml')


@app.route("/sms.xml")
def twilio_sms():
    return render_xml('sms.xml')


@app.route("/callback")
@app.route("/callback.html")
def callback():
    return render_template('callback.html')


if __name__ == "__main__":
    app.debug = True
    app.run()
