import socket
import hashlib

from config import load_config
from datastore import Drinker


# Not the Ego. Not the Super-Ego. The Id.
class Id(object):

    nick = False
    ident = False
    host = False
    ip = False
    fullid = False

    is_authenticated = False
    is_recognized = False
    is_owner = False

    prop = False

    def __init__(self, *arguments, **keywords):

        if not len(arguments) and len(keywords):
            # Prepend 'data__' to all keywords for appropriate searching in data dictfield
            keywords = dict(map(lambda (key, value): ('data__' + str(key), value), keywords.items()))

            # Search for a user with the data field
            self.prop = Drinker.objects(**keywords).first()
            if self.prop:
                self.nick = self.prop.name
        else:
            user = arguments[0]

            self.fullid = user

            try:
                self.nick, self.ident = user.split('!')
                self.host = self.ident.split('@', 1)[1]
            except:
                self.nick = user

            try:
                self.ip = socket.gethostbyname_ex(self.host.strip())[2][0]
            except:
                pass

        if not self.nick:
            return

        # ident not getting set for some reason?

        self.is_recognized = True

        self.prop = Drinker.objects(name=self.nick).first()
        if not self.prop:
            self.prop = Drinker(name=self.nick)
            self.is_recognized = False

        if self.ident in self.prop['idents']:
            self.is_authenticated = True

        secrets = load_config('config/secrets.yaml')

        if self.nick == secrets.owner and self.is_authenticated:
            self.is_owner = True

    # Dynamicaly retrieve data from the datastore connection that are linked to the current
    # authenticated user.
    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, value):
        return self.__setattr__(key, value)

    def __getattr__(self, key):

        if not self.is_recognized or not self.prop:
            return False

        # This can eventually be removed; migrate the data as we go
        self.migrate(key)

        if key in self.prop.data:
            return self.prop.data[key]

        if key in self.prop:
            return self.prop[key]

        return False


    # Update an attribute in the datastore when a linked variable is accessed
    def __setattr__(self, key, value):

        if hasattr(self.__class__, key):
            object.__setattr__(self, key, value)
            return True

        if not self.is_authenticated or not self.prop:
            return False

        # This can eventually be removed; migrate the data as we go
        self.migrate(key)
        self.prop.data[key] = value

        # Even with a migration lets save the changes to the original as well,
        # no need for an additional check.
        if key in self.prop:
            self.prop[key] = value

        try:
            self.prop.save()
        except:
            return False

        return True


    # Migrate data to new data format as we go
    def migrate(self, key):

        protected = ['name', 'password']

        if key in protected: return

        if key in self.prop.data: return

        if key in self.prop:
            self.prop.data[key] = self.prop[key]
            self.prop.save()

        return


    # Set the users password
    def setpassword(self, password, skip_auth_check=False):

        if (not self.is_authenticated or not self.prop) and not skip_auth_check:
            return False

        obj = hashlib.sha256(password)
        self.prop['password'] = obj.hexdigest()

        self.is_authenticated = True

        self.prop.save()

    # Identify a user by password, and add ident if successful
    def identify(self, password):

        obj = hashlib.sha256(password)
        if obj.hexdigest() != self.prop['password']:
            return "Hex check failed."

        self.is_authenticated = True
        self.prop.idents.append(self.ident)

        self.prop.save()

        return True
