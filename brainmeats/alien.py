import praw 
import random

from autonomic import axon, alias, category, help, Dendrite
from settings import NICK
from secrets import REDDIT_APPID, REDDIT_SECRET


@category("alien")
class Alien(Dendrite):
    def __init__(self, cortex):
        super(Alien, self).__init__(cortex)
        user_agent = "MongoBot by /u/locrelite and friends, github.com/huntwelch/MongoBot"
        self.api = praw.Reddit(user_agent=user_agent)

    @axon
    @help("<grab reddit stuff>")
    def reddit(self):
        if not self.values:
            subreddit = False
        else:
            subreddit = self.values[0]

        if subreddit:
            gettum = self.api.get_subreddit(subreddit).get_hot(limit=5)
        else:
            gettum = self.api.get_random_subreddit().get_hot(limit=5)

        # Maybe cache these if the subreddit doesn't change
        entries = ["%s %s" % (str(x), x.short_link) for x in gettum]
        entry = random.choice(entries)

        self.chat(str(entry))
