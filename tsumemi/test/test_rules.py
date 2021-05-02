import unittest

from tsumemi.src.shogi.basetypes import Koma, Side, Square
from tsumemi.src.shogi.position import Position
import tsumemi.src.shogi.rules as rules


class TestMoveGeneration(unittest.TestCase):
    def setUp(self):
        self.position = Position()
        self.position.reset()
        self.rules = rules.Rules()
    
    def test_pawn_moves(self):
        self.position.set_koma(Koma.FU, Square.b34)
        self.position.set_koma(Koma.FU, Square.b57)
        self.position.set_koma(Koma.vFU, Square.b18)
        self.position.set_koma(Koma.vFU, Square.b91)
        self.position.set_koma(Koma.vFU, Square.b33)
        self.position.set_koma(Koma.vFU, Square.b66)
        mvlist = self.rules.generate_moves_fu(pos=self.position, side=Side.GOTE)
        for move in mvlist:
            print(move)
    
    def test_lance_moves(self):
        self.position.set_koma(Koma.KY, Square.b34)
        self.position.set_koma(Koma.KY, Square.b57)
        self.position.set_koma(Koma.vKY, Square.b18)
        self.position.set_koma(Koma.vKY, Square.b91)
        mvlist = self.rules.generate_moves_ky(Side.SENTE, self.position)
        for move in mvlist:
            print(move)