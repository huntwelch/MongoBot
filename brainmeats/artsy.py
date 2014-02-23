import time
import os

from autonomic import axon, alias, help, Dendrite
from settings import IMGS, VIDS, GIFS, WEBSITE, DOWNLOADS
from util import asciiart, savevideo
from moviepy.editor import *


# This monstrous meat (heh) depends on things like
# ffmpeg and all kinds of nastiness ye must install.
# All highly experiemental, and way, way beyond the
# sorts of things that would belong in a bot.
class Artsy(Dendrite):

    types = ['imgs', 'videos']

    def __init__(self, cortex):
        super(Artsy, self).__init__(cortex)

    @axon
    def getvideo(self):
        if not self.values:
            return 'Get what?'

        url = self.values[0]
        self.butler.do('Downloaded video', savevideo, (url, VIDS + '%(title)s.%(ext)s'))

        return 'Downloading'


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
    def gif(self):

        if not self.values or len(self.values) != 3:
            return 'Please enter movie start end.'

        file, start, finis = tuple(self.values)

        vidpath = VIDS + file
        filename = '%s%s.gif' % (time.time(), file)
        gifpath = 'server' + GIFS + filename
        start_m, start_s = tuple(start.split(','))
        start = (int(start_m), float(start_s))

        finis_m, finis_s = tuple(finis.split(','))
        finis = (int(finis_m), float(finis_s))
        
        VideoFileClip(vidpath).subclip(start,finis).resize(0.5).to_gif(gifpath)

        return '%s%s%s' % (WEBSITE, GIFS, filename)
        

    # This not as awesome as I thought it would be,
    # and tends to get cut off by rate limits. The
    # nuts and bolts are in util.py
    @axon
    def ascii(self):
        if not self.values:
            self.chat("Ascii what?")
            return

        path = IMGS + self.values[0]

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
        for file in os.listdir(DOWNLOADS + type):
            if file == '.gitignore':
                continue
            if iter == lim:
                return
            iter += 1
            files.append(file)
        
        return files
