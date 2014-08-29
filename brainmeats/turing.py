from autonomic import axon, help, Dendrite
from datastore import Drinker, Alias
from id import Id

# TO DO:

#    1.) Map +<alias_name> to -ralias so that we can call all aliases as +<alias_name> instead of the longer -ralias <alias_name>
#    2.) Allow for global aliases.
#    3.) Allow exisiting drinker aliases to be promoted to global.
#    4.) List other drinker aliases other than our own.



class Turing(Dendrite):

    def __init__(self, cortex):
        super(Turing, self).__init__(cortex)


    @axon
    def salias(self):
        whom = self.lastsender
        name = self.values[0]
        evil = ['salias', 'ralias', 'lalias', 'dalias']
        definition = ' '.join(self.values[1:])

        drinker = Id(whom)
        # drinker = Drinker.objects(name=whom).first()

        if not drinker.is_authenticated:
            self.chat("Nope.")
            return

        if any(sin in definition for sin in evil):
            self.chat("You're trying to hurt me aren't you?")
            return

        #if not drinker:
        #    drinker = Drinker(name=whom)

        new_alias = Alias(name=name, definition=definition)
        drinker.aliases.append(new_alias)
        # drinker.save()
        self.chat(name + " saved.")

    
    @axon
    def ralias(self):
        name = self.values[0]
        definition = []
        drinker = self._get_drinker()

        if not drinker:
            return

        for alias in drinker.aliases:
            if alias.name == name:
                definition = [elem.strip() for elem in alias.definition.split(';') if len(elem.strip()) > 0]
                for line in definition:
                    self.cx.command(drinker.name, line)
                return


    @axon
    def lalias(self):
        drinker = self._get_drinker()
        if not drinker:
            return

        if len(drinker.aliases) == 0:
            self.chat("Nada.")

        for alias in drinker.aliases:
            self.chat(alias.name + " " + alias.definition)


    @axon
    def dalias(self):
        idx = None
        name = self.values[0]

        if not name:
            self.chat("Much Fat Such Finger")

        drinker = self._get_drinker()
        if not drinker:
            return

        try:
            del_idx = next(idx for (idx, alias) in enumerate(drinker.aliases) if alias.name == name)
        except:
            self.chat("Much Fat Such Finger")
            return

        del drinker.aliases[del_idx]
        if drinker.save():
            self.chat(name + " deleted.")

    def _get_drinker(self):
        drinker = Id(self.lastsender)

        if not drinker.is_authenticated:
            self.chat('Be gone peasant.')
            return None

        return drinker

