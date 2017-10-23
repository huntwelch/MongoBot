import time
import os
import re
import subprocess
import signal

from autonomic import axon, alias, help, Dendrite, public
from util import savevideo
from moviepy.editor import *


# This monstrous meat (heh) depends on things like
# ffmpeg and all kinds of nastiness ye must install.
# All highly experiemental, and way, way beyond the
# sorts of things that belong in a bot.
class Artsy(Dendrite):

    types = ['imgs', 'videos']

    def __init__(self, cortex):
        super(Artsy, self).__init__(cortex)

    @axon
    def getvideo(self):
        if not self.values:
            return 'Get what?'

        url = self.values[0]
        result = savevideo(url, self.cx.settings.media.videos + '/%(title)s.%(ext)s')

        return 'Saved %s' % result


    # So this was a frigging nightmare. Besides
    # requiring ffmpeg and ImageMagick, the
    # excellent moviepy worker throws an IO
    # error that hangs to infinity and beyond.
    # At least, if you're on FreeBSD 9.2 with
    # ffmpeg 2.1.1. OS X? Works fine. On goddamn
    # OS X, the "I'm unix, really-PSYCH! HAHA FUCK
    # YOU!" of operating systems.
    #
    # If you're in a similar spot, you can fix it
    # by removing self.proc.stdout.flush() from
    # video/io/ffmpeg_reader.py around line 121
    # and audio/io/readers.py around line 124, in
    # the installed moviepy lib. Why those lines
    # screw everything up, I don't know. Something
    # about IO. Why Zeus's trollops gettin all up
    # in my code is beyond me.
    @axon
    @help('START FINISH FILE|YOUTUBE_URL <create a gif from a time range in a video>')
    def gif(self):

        # allow for varied input
        # try not to crash, yah?

        if not self.values or len(self.values) != 3:
            return 'Please enter start end filename|youtubeurl.'

        start, finis, target = tuple(self.values)
        timeformat = re.compile('^\d+,\d{2}\.\d{1,2}$')

        # This could all be sorted out better
        if start.find(',') == -1:
            start = '0,' + start

        if finis.find(',') == -1:
            finis = '0,' + finis

        if start.find('.') == -1:
            start = start + '.0'

        if finis.find('.') == -1:
            finis = finis + '.0'

        if not timeformat.match(start) or not timeformat.match(finis):
            self.chat('Times must be in the format 12,34.56 (^\d+,\d{2}\.\d{1,2}$)')
            return

        start_m, start_s = tuple(start.split(','))
        start = (int(start_m), float(start_s))
        finis_m, finis_s = tuple(finis.split(','))
        finis = (int(finis_m), float(finis_s))

        note = 'New gif @ %s'

        youtube = False
        if target.find('www.youtube.com') != -1:
            youtube = True
            target = savevideo(target, self.cx.settings.media.videos + '/%(title)s.%(ext)s')
            target = target.split('/').pop()

        vidpath = '%s/%s' % (self.cx.settings.media.videos, target)

        if not os.path.isfile(vidpath):
            return 'Video file not found'

        filename = '%s%s.gif' % (time.time(), target)
        gifpath = 'server%s%s' % (self.cx.settings.media.gifs, filename)

        try:
            VideoFileClip(vidpath).subclip(start,finis).resize(0.5).to_gif(gifpath)
        except Exception as e:
            return 'Error: %s' % str(e)

        # Because of the above mentioned hack to
        # moviepy, this has to be done to clear
        # the ffmpeg processes. Don't run mongo
        # on dedicated ffmpeg servers.
        p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        for line in out.splitlines():
            if 'ffmpeg' in line:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)

        # I've noticed some people comment lines
        # like this. But, c'mon, it's so freaking
        # obvious what this does and why. Maybe in C
        # it'd need some notes, but python is halfway
        # to pseudocode as it is. I'm not explaining
        # this. Seriously.
        #
        # That said, there's a minor bug that if
        # you've used getvideo to pull a youtube
        # video, then gif it with a link to the
        # original, it will nix the previously
        # downloaded video. It's a little weird to
        # deal with that with the threading and all,
        # and I don't care that much.
        if youtube:
            os.remove(vidpath)

        return '%s%s%s' % (self.cx.settings.website.url, self.cx.settings.website.gifs, filename)

    # This not as awesome as I thought it would be,
    # and tends to get cut off by rate limits.
    @axon
    @help('FILE <make ascii art out of a downloaded file>')
    def ascii(self):
        if not self.values:
            self.chat("Ascii what?")
            return

        path = '%s/%s' % (self.cx.settings.media.images, self.values[0])

        try:
            preview = asciiart(path)
        except:
            self.chat("Couldn't render.")
            return

        if not preview:
            self.chat("Couldn't render.")
            return

        lines = preview.split("\n")
        for line in lines:
            time.sleep(1)
            self.chat(line)

    @axon
    @help('[imgs|videos] <show downloaded items>')
    def downloads(self):

        if not self.values:
            type = 'imgs'
        else:
            type = self.values[0]

        if type not in self.types:
            return 'No files of that type. Use "imgs" or "videos"'

        iter = 0
        lim=5
        files = []
        for file in os.listdir('%s/%s' % (self.cx.settings.media.downloads, type)):
            if file == '.gitignore':
                continue
            if iter == lim:
                return
            iter += 1
            files.append(file)

        return files

# http://stevendkay.wordpress.com/2009/09/08/generating-ascii-art-from-photographs-in-python/
# Couldn't have done this with the above link,
# but there are some problems with the script:
# if you adapt from it, don't use 'str' as a
# variable name unless you want some troubling
# error messages when you try to debug by casting
# exceptions with str(), and im = im.thumbnail
# modifies the original and returns None, so im
# is no longer usable.
def asciiart(image_path):
    if image_path.find('/') != -1:
        return

    greyscale = [" "," ",".,-","_ivc=!/|\\~","gjez2]/(YL)t[+T7Vf","mdK4ZGbNDXY5P*Q","W8KMA","#%$"]
    zonebounds=[36,72,108,144,180,216,252]
    size = 30
    out = ""

    img = Image.open(image_path)
    img.thumbnail((size, size), Image.ANTIALIAS)
    img = img.resize((size*2, size))
    img = img.convert("L")

    for y in range(0,img.size[1]):
        for x in range(0,img.size[0]):
            lum = 255 - img.getpixel((x,y))
            row = bisect(zonebounds,lum)
            possibles = greyscale[row]
            out += possibles[random.randint(0,len(possibles)-1)]
        out += "\n"

    return out

