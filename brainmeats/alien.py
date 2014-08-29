import praw
import random

from autonomic import axon, alias, help, Dendrite

# It's called 'alien' because (re)ddit conflicted
# with (re)ference in the help menu.
class Alien(Dendrite):

    user_agent = "MongoBot by /u/locrelite and friends, github.com/huntwelch/MongoBot"
    api = praw.Reddit(user_agent=user_agent)
    last = False

    def __init__(self, cortex):
        super(Alien, self).__init__(cortex)


    @axon
    @help("<grab reddit stuff>")
    @alias('r')
    def reddit(self):
        subreddit = False
        if not self.values:
            if self.last:
                subreddit = self.last
            else:
                # currently broken if blank, so:
                return "Enter a subreddit"
        else:
            subreddit = self.values[0]
            self.last = subreddit

        try:
            if subreddit:
                gettum = self.api.get_subreddit(subreddit).get_hot(limit=5)
            else:
                # this is borked for whatever reason
                gettum = self.api.get_random_subreddit().get_hot(limit=5)

            # Maybe cache these if the subreddit doesn't change
            entries = ["%s %s" % (str(x), x.short_link) for x in gettum]
            entry = random.choice(entries)

        except Exception as e:
            self.chat('Reddit fail.', str(e))
            return

        return str(entry)
