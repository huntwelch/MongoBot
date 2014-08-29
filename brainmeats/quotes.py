import random

from autonomic import axon, help, Dendrite
from datastore import Quote
from datetime import datetime


class Quotes(Dendrite):
    def __init__(self, cortex):
        super(Quotes, self).__init__(cortex)


    @axon
    @help("QUOTE <add quote to database>")
    def addquote(self):
        adder = self.lastsender

        if not self.values:
            self.chat("No")
            return

        text = ' '.join(self.values)

        quote = Quote(adder=adder,
                      text=text,
                      date=datetime.utcnow(),
                      random=random.random())
        quote.save()
        return 'Quote saved'


    @axon
    @help("<show a random quote>")
    def randomquote(self):
        rand = random.random()

        if not Quote.objects:
            self.chat("no quotes")
            return

        q = random.choice(Quote.objects)

        # We can use this way if the QDB gets big.  This comes from the
        # official MongoDB cookbook.  We can use the random field for the
        # search function below too.  For that, need to query on the text and
        # random.
        if False:
            q = Quote.objects(random__gte=rand).first()
            if not q:
                q = Quote.objects(random__lte=rand).first()

        if q:
            return q.text
        else:
            return "Couldn't find a quote for some reason"


    @axon
    @help("SEARCH_TERM <search for a quote>")
    def quote(self):
        if not self.values:
            self.chat("Enter a search term")
            return

        term = ' '.join(self.values)

        if len(term) <= 1:
            self.chat("Enter a bigger search term")
            return

        quotes = Quote.objects(text__icontains=term)

        if not quotes:
            self.chat("No quotes found")
        else:
            total = len(quotes)
            if total > 1:
                q = random.choice(quotes)
            else:
                q = quotes.first()
            self.chat(q.text)


    @axon
    @help("SEARCH_TERM <returns the count of the quotes found")
    def countquote(self):
        if not self.values:
            self.chat("Enter a search term")
            return

        term = ' '.join(self.values)

        if len(term) <= 1:
            self.chat("Enter a bigger search term")
            return

        quotes = Quote.objects(text__icontains=term)

        if not quotes:
            self.chat("No quotes found")
        else:
            total = len(quotes)
            self.chat("Found %d quotes" % total)
