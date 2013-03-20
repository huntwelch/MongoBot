from datastore import Drinker, Position, connectdb


def clear():
    for drinker in Drinker.objects:
        drinker.cash = 100000
        drinker.positions = []
        drinker.save()

if __name__ == '__main__':
    connectdb()
    clear()
