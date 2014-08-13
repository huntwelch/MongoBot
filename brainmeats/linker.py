import re

from pprint import pprint
from autonomic import axon, help, Dendrite, Cerebellum, Receptor, Synapse
from util import shorten, unescape
from staff import Browser
from random import randint

@Cerebellum
class Linker(Dendrite):

    '''
    Set up the brainmeat
    '''
    def __init__(self, cortex):
        super(Linker, self).__init__(cortex)


    '''
    urlfinder locates urls in incoming irc messages
    '''
    @Receptor('IRC_PRIVMSG')
    def urlfinder(self, source, args):
        pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        match_urls = re.compile(pattern)
        urls = match_urls.findall(args[-1])

        for url in urls:
            self.urlparse(url)

        return

    @Synapse('url')
    def urlparse(self, url):
        if self.cleanse(url) == False:
            return [url]

        fubs = 0
        title = "Couldn't get title"

        site = Browser(url)

        if site.error:
            self.chat('Total fail: %s' % site.error)
            return [url]

        roasted = shorten(url)
        if not roasted:
            roasted = "Couldn't roast"
            fubs += 1

        self.chat('%s @ %s' % (unescape(site.title()), roasted))
        return [url]

    def cleanse(self, url):
        # Don't parse certain URLs - return false for these
        if (url.find('roa.st') != -1 or
            url.find('gist.github') != -1 or
            url.find('twitter.com') != -1):
            return False

        # Also ignore certain file types - there are special handlers for
        # them...

        return

    @Receptor('url')
    def random_tweet(self, url):

        if self.cleanse(url) == False:
            return

        if randint(1, 5) == 1:
            try:
                self.cx.commands.get('tweet')(url)
            except:
                pass


