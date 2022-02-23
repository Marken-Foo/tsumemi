import unittest

from tsumemi.src.shogi.basetypes import KomaType, Side, Square
from tsumemi.src.shogi.notation_writer import WESTERN_MOVE_FORMAT, WesternMoveWriter
from tsumemi.src.shogi.position import Position


class TestWesternNotation(unittest.TestCase):
    def setUp(self):
        sfen = r"9/7+R1/sS1+p1+P2+R/2p+P1+P3/SS1n+pn3/9/9/9/3N5 b 2S2s 1"
        self.position = Position()
        self.position.from_sfen(sfen)
        self.move_writer = WesternMoveWriter(WESTERN_MOVE_FORMAT)
    
    def test_move(self):
        move = self.position.create_move(Square.b69, Square.b57)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("N-57", movestr)
    
    def test_gote_move(self):
        move = self.position.create_move(Square.b93, Square.b94)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("S-94", movestr)
    
    def test_capture(self):
        move = self.position.create_move(Square.b64, Square.b74)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("+Px74", movestr)
    
    def test_drop(self):
        move = self.position.create_drop_move(Side.SENTE, KomaType.GI, Square.b84)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("S*84", movestr)
    
    def test_disambiguation(self):
        move = self.position.create_move(Square.b85, Square.b94)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("S(85)-94", movestr)
    
    def test_promotion(self):
        move = self.position.create_move(Square.b45, Square.b37, is_promotion=True)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("N-37+", movestr)
    
    def test_nonpromotion(self):
        move = self.position.create_move(Square.b45, Square.b37, is_promotion=False)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("N-37=", movestr)
    
    def test_promotion_and_disambiguation(self):
        move = self.position.create_move(Square.b65, Square.b57, is_promotion=True)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("N(65)-57+", movestr)
    
    def test_nonpromotion_and_disambiguation(self):
        move = self.position.create_move(Square.b45, Square.b57, is_promotion=False)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("N(45)-57=", movestr)
    
    def test_promotion_as_disambiguation(self):
        move = self.position.create_move(Square.b83, Square.b94, is_promotion=True)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("S94+", movestr)
    
    def test_nonpromotion_as_disambiguation(self):
        move = self.position.create_move(Square.b83, Square.b94, is_promotion=False)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("S94=", movestr)
    
    def test_cannot_promote_as_disambiguation(self):
        move = self.position.create_move(Square.b85, Square.b74)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("Sx74", movestr)