import tweepy
import re

from autonomic import axon, alias, help, Dendrite, Cerebellum, Receptor, public
from cybernetics import metacortex

@Cerebellum
class Twitting(Dendrite):

    api = False
    lasttweet = False

    def __init__(self, cortex):
        super(Twitting, self).__init__(cortex)

        self.auth = tweepy.OAuthHandler(self.secrets.consumerkey, self.secrets.consumersecret)
        self.auth.set_access_token(self.secrets.accesstoken, self.secrets.accesssecret)
        self.api = tweepy.API(self.auth)


    @axon
    @help('<show link to %s\'s twitter feed>' % metacortex.botnick)
    def totw(self):
        return self.config.page


    @axon
    @help('[ID] <retweet by id, or just the last tweet>')
    def retweet(self):
        id = self.lasttweet
        if not self.values and not id:
            self.chat('Provide an id or link a tweet first')
            return

        if self.values:
            id = self.values[0]

        try:
            status = self.api.retweet(id)
        except Exception as e:
            return 'Twitter error: %s' % str(e)

        return 'Retwitted'


    @axon
    @help('MESSAGE <post to %s\'s twitter feed>' % metacortex.botnick)
    def tweet(self, _message=False):
        if not self.values and not _message:
            self.chat('Tweet what?')
            return

        if not _message:
            message = ' '.join(self.values)
        else:
            message = _message

        try:
            status = self.api.update_status(message)
        except Exception as e:
            return 'Twitter error: %s' % str(e)

        if not _message:
            return 'Twitted'


    @axon
    @help('ID <retrieve the tweet with ID>')
    def get_tweet(self, id=False):
        if not id:
            id = '+'.join(self.values)

        self.lasttweet = id

        status = self.api.get_status(id)

        text = status.text
        screen_name = status.user.screen_name
        name = status.user.name
        if status.text:
            return '%s (%s) tweeted: %s' % (name, screen_name, text)


    @Receptor('url')
    def auto_get_tweet(self, url):
        get_twitter_id = re.compile('http[s]?://[www\.]?twitter\.com/.+/status/([0-9]+)')
        twitter_id = get_twitter_id.findall(url)

        if len(twitter_id):
            try:
                self.chat(self.get_tweet(twitter_id.pop()))
            except:
                self.chat('Could not get the tweet.')

        return

