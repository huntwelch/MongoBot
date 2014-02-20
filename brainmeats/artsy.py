import time

from autonomic import axon, alias, help, Dendrite
from settings import IMGS, VIDS, GIFS, WEBSITE
from util import asciiart, getyoutube
from moviepy.editor import *


# This monstrous meat (heh) depends on things like
# ffmpeg and all kinds of nastiness ye must install.
# All highly experiemental, and way, way beyond the
# sorts of things that would belong in a bot.
class Artsy(Dendrite):

    types = ['imgs', 'vids']

    def __init__(self, cortex):
        super(Artsy, self).__init__(cortex)

    @axon
    def getvideo(self):
        if not self.values:
            return 'Get what?'

        url = self.values[0]
        getyoutube(url, VIDS + '%(title)s.%(ext)s')

        return 'Downloading'

    @axon
    def gif(self):
        #if not self.values or len(self.values) != 3:
        #    return 'Please enter movie start end.'

        #file, start, finis = tuple(self.values)

        file, start, finis = tuple(['candh.mp4', '1,20.10', '1,20.80'])

        print 'Got values'
        vidpath = VIDS + file
        filename = '%s.gif' % file
        gifpath = GIFS + filename
        start_m, start_s = tuple(start.split(','))
        start = (int(start_m), float(start_s))

        finis_m, finis_s = tuple(finis.split(','))
        finis = (int(finis_m), float(finis_s))
        
        print vidpath
        print gifpath
        print start
        print finis

        try:
            print 'Figuring it out'
            VideoFileClip(vidpath)#.subclip(start,finis).resize(0.5).to_gif(gifpath)
            print 'Woot!'
        except Exception as e:
            self.chat('Borked.', str(e))
            return

        print 'Done'
        return '%s/%s%s' % (WEBSITE, GIFS, filename)
        

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
            return 'No files of that type.'
        
        iter = 0
        lim=5
        files = []
        for file in os.listdir(IMGS):
            if file == '.gitignore':
                continue
            if iter == lim:
                return
            iter += 1
            files.append(file)
        
        return files
