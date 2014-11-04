import time 
import urllib 
import simplejson

from hashlib import md5

from autonomic import axon, alias, help, Dendrite, Cerebellum, Synapse
from staff import Browser

# TODO: recall ids after searches, so -events will 
# fetch characters etc. See api

# Just in case this whole damn bot wasn't 
# nerdy enough.
@Cerebellum
class Marvel(Dendrite):

    def __init__(self, cortex):
        super(Marvel, self).__init__(cortex)


    def _call(self, params):
        ts = str(time.time())
        hashed = md5(ts + self.secrets.privatekey + self.secrets.publickey).hexdigest()

        category = params['category']
        del params['category']

        params.update({
            'ts': ts,
            'apikey': self.secrets.publickey,
            'hash': hashed,
        })

        self.apiurl = '%s%s?%s' % (self.config.gateway, category, urllib.urlencode(params))

        return self.apiurl


    @axon
    def character(self):
        link = self._call({
            'category': 'characters',
            'name': ' '.join(self.values),
        })
        
        data = simplejson.loads(Browser(link).read())

        return data['results'][0]['description']
