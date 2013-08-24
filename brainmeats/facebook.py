from autonomic import axon, alias, category, help, Dendrite
from secrets import FB_USER, FB_PASS, FB_PAGE, FB_MONGOBOT_APPID, FB_MONGOBOT_SECRET
from settings import NICK


@category("facebook")
class Facebook(Dendrite):
    def __init__(self, cortex):
        super(Facebook, self).__init__(cortex)

    @axon
    @help("<show link to " + NICK + "'s community page>")
    def tofb(self):
        self.chat(FB_PAGE)
        return
