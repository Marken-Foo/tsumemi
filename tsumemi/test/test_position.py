import unittest

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Side, Square
from tsumemi.src.shogi.position import Position


class TestPositionMethods(unittest.TestCase):
    def setUp(self):
        self.position = Position()
        self.position.reset()
    
    def test_king_is_not_promoted(self):
        self.assertFalse(KomaType.get(Koma.OU).is_promoted())
    
    def test_set_koma(self):
        self.position.set_koma(Koma.vTO, Square.b63)
        self.assertEqual(self.position.get_koma(sq=Square.b63), Koma.vTO)
    
    def test_set_hand_koma_count(self):
        self.position.set_hand_koma_count(Side.SHITATE, Koma.KE, 4)
        self.assertEqual(self.position.get_hand(Side.SENTE)[Koma.KE], 4)
    
    def test_make_move(self):
        self.position.set_koma(Koma.vGI, Square.b76)
        self.position.set_koma(Koma.UM, Square.b87)
        move = Move(start_sq=Square.b76, end_sq=Square.b87, is_promotion=True, koma=Koma.vGI, captured=Koma.UM)
        self.position.make_move(move)
        self.assertEqual(self.position.get_koma(sq=Square.b87), Koma.vNG)
        self.assertEqual(self.position.get_hand(Side.GOTE)[Koma.KA], 1)
    
    def test_from_to_sfen(self):
        sfen = "nk1n5/1g3g3/p8/2BP5/3+r5/9/9/9/9 b RBGg4s2n4l16p 17"
        self.position.from_sfen(sfen)
        self.assertEqual(self.position.to_sfen(), sfen)
    
    def test_starting_position(self):
        sfen_hirate = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
        self.position.from_sfen(sfen_hirate)
        self.assertEqual(self.position.to_sfen(), sfen_hirate)
