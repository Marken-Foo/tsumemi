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
        mvlist = self.rules.generate_pawn_moves(Side.GOTE, self.position)
        for move in mvlist:
            print(move)