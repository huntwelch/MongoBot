import os

from time import mktime, localtime, sleep

while True:
    sleep(30)
    pulse = open('/tmp/bot.pulse', 'r')
    lastpulse = pulse.readline()
    if mktime(localtime()) - float(lastpulse) > 25:
        os.system("ps ax | grep 'medulla.py' | grep -v grep | awk '{print $1}' | xargs kill")
