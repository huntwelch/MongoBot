from autonomic import axon, alias, help, Dendrite
from settings import WEBSITE


# Settings

Countries = {
    'Austria': {
       'color': 'red', 
       'opening_positions': {'Vienna':'A', 'Budapest':'A', 'Trieste':'F'},
    },
    'England': {
       'color': 'blue', 
       'opening_positions': {'Liverpool':'A', 'London':'F', 'Edinburgh':'F'},
    },
    'France': {
       'color': 'pink', 
       'opening_positions': {'Paris':'A', 'Marseilles':'A', 'Brest':'F'},
    },
    'Germany': {
       'color': 'black', 
       'opening_positions': {'Berlin':'A', 'Munich':'A', 'Kiel':'F'},
    },
    'Italy': {
       'color': 'green', 
       'opening_positions': {'Rome':'A', 'Venice':'A', 'Naples':'F'},
    },
    'Russia': {
       'color': 'white', 
       'opening_positions': {'Moscow':'A', 'Warsaw':'A', 'Sevastopol':'F', 'St_Petersburg':'F'},
    },
    'Turkey': {
       'color': 'yellow', 
       'opening_positions': {'Constantinople':'A', 'Smyrna':'A', 'Ankara':'F'},
    },
}

class Diplomacy(Dendrite):
    def __init__(self, cortex):
        super(Diplomacy, self).__init__(cortex)

    @axon
    @help("<get link to diplomacy board>")
    def diplomacy(self):
        link = WEBSITE + "/diplomacy"
        self.chat(link)

