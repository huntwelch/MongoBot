import twitter

from autonomic import axon, alias, category, help, Dendrite
from settings import NICK
from secrets import (TWIT_USER, TWIT_PASS, TWIT_ACCESS_TOKEN, TWIT_ACCESS_SECRET,
                     TWIT_CONSUMER_KEY, TWIT_CONSUMER_SECRET, TWIT_PAGE)


@category("twitter")
class Twitterapi(Dendrite):
    def __init__(self, cortex):
        super(Twitterapi, self).__init__(cortex)

        self.api = twitter.Api(consumer_key=TWIT_CONSUMER_KEY,
                               consumer_secret=TWIT_CONSUMER_SECRET,
                               access_token_key=TWIT_ACCESS_TOKEN,
                               access_token_secret=TWIT_ACCESS_SECRET)

    @axon
    @help("<show link to " + NICK + "'s twitter feed>")
    def totw(self):
        self.chat(TWIT_PAGE)

    @axon
    @help("MESSAGE <post to " + NICK + "'s twitter feed>")
    def tweet(self, _message=False):
        if not self.values and not _message:
            self.chat("Tweet what?")
            return

        if not _message:
            message = ' '.join(self.values)
        else:
            message = _message

        status = self.api.PostUpdate(message)

        if not _message:
            self.chat('Tweeted "' + status.text + '"')

    @axon
    @help("ID <retrieve the tweet with ID>")
    def get_tweet(self):
        status = self.api.GetStatus('+'.join(self.values))

        text = status.text
        screen_name = status.user.screen_name
        name = status.user.name
        if status.text:
            self.chat('%s (%s) tweeted: %s' % (name, screen_name, text))
