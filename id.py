from config import load_config
from datastore import Drinker
from pprint import pprint

'''
Not the Ego. Not the Super-Ego. The Id.
'''
class Id(object):

    nick = False
    ident = False
    host = False

    is_authenticated = False
    is_guest = False
    is_owner = False

    prop = False

    def __init__(self, user):

        try:
            self.nick, data = user.split('!')
            self.ident, self.host = data.split('@')
        except Exception as e:
            pprint(e)
            return

        settings = load_config('config/settings.yaml')
        auth_data = load_config(settings.directory.authfile)

        if self.nick in auth_data:
            self.is_authenticated = True

            if 'owner' in auth_data[self.nick] and auth_data[self.nick].owner:
                self.is_owner = True

            self.prop = Drinker.objects(name=self.nick).first()
            if not self.prop:
                self.prop = Drinker(name=self.nick)


    '''
    Dynamicaly retrieve data from the datastore connection that are linked to the current
    authenticated user.
    '''
    def __getattr__(self, key):

        if not self.is_authenticated or not self.prop:
            return False

        if key in self.prop:
            return self.prop[key]

        if key in self.prop.data:
            return self.prop.data[key]

        return False


    '''
    Update an attribute in the datastore when a linked variable is accessed
    '''
    def __setattr__(self, key, value):

        if hasattr(self.__class__, key):
            object.__setattr__(self, key, value)
            return True

        if not self.is_authenticated or not self.prop:
            return False

        if key in self.prop:
            self.prop[key] = value
        else:
            self.prop.data[key] = value

        try:
            self.prop.save()
        except:
            return False

        return True


