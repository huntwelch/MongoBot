from autonomic import axon, category, help, Dendrite


# This isn't actually playable without an 
# enormous ammount of trust between the players.
# Always wanted to do more with it, but, well,
# I haven't.
@category("chess")
class Chess(Dendrite):
    def __init__(self, cortex):
        super(Chess, self).__init__(cortex)

        self.pieces = dict(
            br=u'\u265c',
            bn=u'\u265e',
            bb=u'\u265d',
            bq=u'\u265b',
            bk=u'\u265a',
            bp=u'\u265f',
            wr=u'\u2656',
            wn=u'\u2658',
            wb=u'\u2657',
            wq=u'\u2655',
            wk=u'\u2654',
            wp=u'\u2659',
        )

        self.basegrid = [
            ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
            ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
            ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr'],
        ]

        self.chessgrid = self.basegrid

    @axon
    @help("<reset chessboard>")
    def resetchess(self):
        self.chessgrid = self.basegrid

    @axon
    @help("<show chessboard>")
    def chess(self):
        squares = [u'\u25fc', u'\u25fb']
        flip = 0
        count = 8
        for row in self.chessgrid:
            rowset = [str(count)]
            for space in row:
                if space:
                    rowset.append(self.pieces[space])
                else:
                    rowset.append(squares[flip])
                flip = (flip + 1) % 2

            flip = (flip + 1) % 2
            count -= 1

            self.chat(' '.join(rowset))

        self.chat(u'  a\u00a0b\u00a0c\u00a0d\u00a0e\u00a0f\u00a0g\u00a0h')

    @axon
    @help("[a-f][1-8] [a-f][1-8] <move piece [from] [to]>")
    def move(self):
        if not self.values:
            self.chat("Bad format")
            return

        if len(self.values) < 2:
            self.chat("Not enough values")
            return

        start = self.values[0]
        finis = self.values[1]
        trans = dict(a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7)

        if start in self.pieces:
            piece = self.pieces[start]
        else:
            x = 8 - int(start[1:])
            y = trans[start[:1]]

            piece = self.chessgrid[x][y]
            if not piece:
                self.chat("No piece there")
                return
            self.chessgrid[x][y] = ''

        x = 8 - int(finis[1:])
        y = trans[finis[:1]]

        self.chessgrid[x][y] = piece
        self.chess()
