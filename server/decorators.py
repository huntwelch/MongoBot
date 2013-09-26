import os

from functools import wraps
from flask import request, Response
from secrets import HTTP_USER, HTTP_PASS
from settings import ONETIME


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == HTTP_USER and password == HTTP_PASS

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        if request.args.get('onetime'):
            try:
                file = open(ONETIME, 'r')
                current = file.readline()
                file.close()

                print current == request.args.get('onetime')

                if request.args.get('onetime') == current:
                    os.remove(ONETIME)
                    return f(*args, **kwargs)
            except:
                print "Failed to open"

        auth = request.authorization

        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
