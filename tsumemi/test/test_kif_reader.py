import unittest

from io import StringIO

from tsumemi.src.tsumemi.kif_parser import KifReader, Piece


class TestKifReader(unittest.TestCase):
    '''Tests for the unit-testable parts of the KifReader class.'''
    test_board = "  ９ ８ ７ ６ ５ ４ ３ ２ １\n" +\
    "+---------------------------+\n" +\
    "| ・ ・ ・ ・ ・ ・ ・v桂v香|一\n" +\
    "| ・ ・ ・ ・ ・ ・ ・ ・ ・|二\n" +\
    "| ・ ・ ・ ・ と 角v玉v歩 ・|三\n" +\
    "| ・ ・ ・ ・ ・ ・ ・ ・v歩|四\n" +\
    "| ・ ・ ・ ・ ・ ・ ・ ・ ・|五\n" +\
    "| ・ ・ ・ ・ ・ ・ 歩 ・ 歩|六\n" +\
    "| ・ ・ ・ ・ ・ ・ ・ ・ ・|七\n" +\
    "| ・ ・ ・ ・ ・ ・ ・ ・ ・|八\n" +\
    "| ・ ・ ・ ・ ・ ・ ・ ・ 香|九\n" +\
    "+---------------------------+\n"
    
    def setUp(self):
        self.reader = KifReader()
    
    def tearDown(self):
        self.reader = None
    
    def make_hand(self, arr):
        # Take array of ints, make hand with that many pieces.
        # Order is hisha-kaku-kin-gin-kei-kyou-fu.
        hand = []
        piece_types = [Piece.HISHA, Piece.KAKU, Piece.KIN, Piece.GIN,
                       Piece.KEI, Piece.KYOU, Piece.FU]
        for num, type in zip(arr, piece_types):
            hand.extend([type] * num)
        return hand
    
    def test_read_hand_line(self):
        # half-width space, trailing space
        line = "後手の持駒：飛 角 金二 銀三 桂四 香四 歩十六 "
        answer = self.make_hand([1, 1, 2, 3, 4, 4, 16])
        pieces = self.reader.parse_hand(handle=None, line=line)
        self.assertEqual(pieces, answer)
    
    def test_read_hand_line(self):
        # full-width space, no trailing space
        line = "先手の持駒：飛　桂"
        answer = self.make_hand([1, 0, 0, 0, 1, 0, 0])
        pieces = self.reader.parse_hand(handle=None, line=line)
        self.assertEqual(pieces, answer)
    
    def test_read_hand_line_nashi(self):
        line = "後手の持駒：なし"
        answer = self.make_hand([0] * 7)
        pieces = self.reader.parse_hand(handle=None, line=line)
        self.assertEqual(pieces, answer)
    
    def test_read_hand_handle(self):
        handle = StringIO("後手の持駒：飛 角 銀三 桂 香四 \n")
        answer = self.make_hand([1, 1, 0, 3, 1, 4, 0])
        pieces = self.reader.parse_hand(handle=handle)
        self.assertEqual(pieces, answer)
    
    def test_read_board(self):
        handle = StringIO(self.test_board)
        sente, gote = self.reader.parse_board(handle=handle)
        answer_sente = [[Piece.NONE] * 9 for i in range(9)]
        answer_gote = [[Piece.NONE] * 9 for i in range(9)]
        answer_sente[2][4] = Piece.TOKIN
        answer_sente[2][5] = Piece.KAKU
        answer_sente[5][6] = Piece.FU
        answer_sente[5][8] = Piece.FU
        answer_sente[8][8] = Piece.KYOU
        answer_gote[0][7] = Piece.KEI
        answer_gote[0][8] = Piece.KYOU
        answer_gote[2][6] = Piece.GYOKU
        answer_gote[2][7] = Piece.FU
        answer_gote[3][8] = Piece.FU
        self.assertEqual(sente, answer_sente)
        self.assertEqual(gote, answer_gote)
