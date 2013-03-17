#!/usr/bin/env python
STRAIGHT_FLUSH = 8
FOUR_OF_A_KIND = 7
FULL_HOUSE = 6
FLUSH = 5
STRAIGHT = 4
THREE_OF_A_KIND = 3
TWO_PAIR = 2
PAIR = 1
HIGH_CARD = 0

HAND_NAMES = ("HIGH_CARD", "PAIR", "TWO_PAIR", "THREE_OF_A_KIND", "STRAIGHT",
              "FLUSH", "FULL_HOUSE", "FOUR_OF_A_KIND", "STRAIGHT_FLUSH")




class Card(object):
    #SUITS = ['s', 'h', 'd', 'c']
    SUITS = [u"\u2660", u"\u2665", u"\u2666", u"\u2663"]
    RANKS = "A23456789TJQKA"

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        rank = self.RANKS[self.rank]
        if rank == 'T':
            rank = '10'
        rep = u"%s%s" % (rank, self.SUITS[self.suit - 1])
        return rep.encode('utf-8')

    def encoded(self):
        return self.suit * 13 + self.rank


def cmp_rank(x, y):
    return y.rank - x.rank


def cmp_suit_rank(x, y):
    return y.rank - x.rank if x.suit == y.suit else x.suit - y.suit


def initialize_deck():
    for suit in range(1, 5):
        for rank in range(1, 14):
            deck.append(Card(suit, rank))


def find_straight_flush(cards):
    cards_aces_high = cards
    cards_aces_low = [Card(x.suit, 0) if x.rank == 13 else x for x in cards]

    for cards in (cards_aces_high, cards_aces_low):
        cards.sort(cmp=cmp_suit_rank)
        for i in range(3):
            high = cards[i]
            low = cards[i + 4]
            if low.suit == high.suit and high.rank == low.rank + 4:
                return (STRAIGHT_FLUSH, cards[i:i + 5], [])
    return None


def find_four_of_a_kind(cards):
    cards.sort(cmp=cmp_rank)
    for i in range(4):
        if cards[i].rank == cards[i + 3].rank:
            hand = cards[i:i + 4]
            rest = cards[0:i] + cards[i + 4:7]
            return (FOUR_OF_A_KIND, hand, [rest[0]])
    return None


def find_full_house(cards):
    cards.sort(cmp=cmp_rank)
    for i in range(5):
        if cards[i].rank == cards[i + 2].rank:
            hand = cards[i:i + 3]
            rest = cards[0:i] + cards[i + 3:7]
            for j in range(3):
                if rest[j].rank == rest[j + 1].rank:
                    hand += rest[j:j + 2]
                    return (FULL_HOUSE, hand, [])


def find_flush(cards):
    cards.sort(cmp=cmp_suit_rank)
    for i in range(3):
        if cards[i].suit == cards[i + 4].suit:
            return (FLUSH, cards[i:i + 5], [])


def find_straight(cards):
    cards_aces_high = cards
    cards_aces_low = [Card(x.suit, 0) if x.rank == 13 else x for x in cards]

    for cards in (cards_aces_high, cards_aces_low):
        # Sort and remove cards with duplicated ranks
        cards.sort(cmp=cmp_rank)
        cards = [cards[i] for i in range(len(cards)) if cards[i].rank != cards[i - 1].rank]
        for i in range(len(cards) - 5 + 1):
            if cards[i].rank == cards[i + 4].rank + 4:
                return (STRAIGHT, cards[i:i + 5], [])
    return None


def find_three_of_a_kind(cards):
    cards.sort(cmp=cmp_rank)
    for i in range(5):
        if cards[i].rank == cards[i + 2].rank:
            hand = cards[i:i + 3]
            rest = cards[0:i] + cards[i + 3:7]
            return (THREE_OF_A_KIND, hand, rest[:2])
    return None


def find_two_pair(cards):
    cards.sort(cmp=cmp_rank)
    for i in range(6):
        if cards[i].rank == cards[i + 1].rank:
            hand = cards[i:i + 2]
            rest = cards[0:i] + cards[i + 2:7]
            for j in range(4):
                if rest[j].rank == rest[j + 1].rank:
                    hand += rest[j:j + 2]
                    rest = rest[0:j] + rest[j + 2:5]
                    return (TWO_PAIR, hand, [rest[0]])
    return None


def find_pair(cards):
    cards.sort(cmp=cmp_rank)
    for i in range(6):
        if cards[i].rank == cards[i + 1].rank:
            hand = cards[i:i + 2]
            rest = cards[0:i] + cards[i + 2:7]
            return (PAIR, hand, rest[:3])
    return None


def find_high_card(cards):
    cards.sort(cmp=cmp_rank)
    return (HIGH_CARD, [cards[0]], cards[1:5])


def find_best_hand(cards):
    for func in [find_straight_flush,
                 find_four_of_a_kind,
                 find_full_house,
                 find_flush,
                 find_straight,
                 find_three_of_a_kind,
                 find_two_pair,
                 find_pair,
                 find_high_card
                 ]:
        res = func(cards)
        if res is not None:
            return res


def get_ranks(x):
    return [i.rank for i in x]


def cmp_hands(x, y):
    if x[0] == y[0]:
        xhr = get_ranks(x[1])
        yhr = get_ranks(y[1])
        if (xhr == yhr):
            xkr = get_ranks(x[2])
            ykr = get_ranks(y[2])
            if xkr == ykr:
                return 0
            elif xkr < ykr:
                return 1
            else:
                return -1
        elif xhr < yhr:
            return 1
        else:
            return -1
    else:
        return y[0] - x[0]


def find_winners(hands):
    best_type = max([h[0] for h in hands])
    hands = filter(lambda x: x[0] == best_type, hands)

    if len(hands) == 1:
        return [hands[0][3]]

    for i in range(len(hands)):
        hand = hands[i]
        hands[i] = (hand[0],
                    [h.rank for h in hand[1]],
                    [h.rank for h in hand[2]],
                    hand[3])
    best_hand = max([h[1] for h in hands])
    hands = filter(lambda x: x[1] == best_hand, hands)
    if len(hands) == 1:
        return [hands[0][3]]

    best_kicker = max([h[2] for h in hands])
    hands = filter(lambda x: x[2] == best_kicker, hands)

    return [h[3] for h in hands]
