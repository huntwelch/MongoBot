import os

from time import mktime, localtime, sleep
from config import load_config

# The doctor checkout the pulse file set by
# medulla. If it's been gone too long,
# according to PULSE_RATE, it kills it
# with some awkward command line fu.

settings = load_config('config/settings.yaml')

print "The doctor is in"
while True:
    pulse = open(settings.sys.pulse, 'r')
    lastpulse = pulse.readline()

    try:
        if mktime(localtime()) - float(lastpulse) > PULSE_RATE:
            print "He's dead, Jim"
            os.system("ps ax | grep 'medulla.py' | grep -v grep | awk '{print $1}' | xargs kill")
            os.system("python medulla.py >> hippocampus/log/sys.log 2>>hippocampus/log/error.log &")
            print "It's cool, we had the thingy"
    except Exception as e:
        print e
        pass

    sleep(10)
