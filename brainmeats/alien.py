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
    @help("<>")
    def reddit(self):
        entries = self.api.get_subreddit('funny').get_hot(limit=20)
        entry = random.choice(entries)
        self.chat(str(entry))
