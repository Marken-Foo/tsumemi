import unittest

import itertools

from tsumemi.src.shogi.basetypes import GameTermination, KomaType, Side
from tsumemi.src.shogi.move import TerminationMove
from tsumemi.src.shogi.notation import JapaneseMoveWriter, WesternMoveWriter
from tsumemi.src.shogi.position import Position
from tsumemi.src.shogi.square import Square


class TestWesternNotation(unittest.TestCase):
    def setUp(self):
        self.position = Position()
        self.move_writer = WesternMoveWriter()

    def _parse_move_test(self, line1, line2, line3):
        test_name = line1.rstrip()
        sfen = line2.rstrip()
        (start_coord, end_coord, promotion, expected_movestr) = line3.rstrip().split(
            " "
        )

        self.position.from_sfen(sfen)
        start_sq = Square.from_coord(int(start_coord))
        end_sq = Square.from_coord(int(end_coord))
        is_promotion = promotion == "+"
        move = self.position.create_move(start_sq, end_sq, is_promotion)
        return test_name, move, expected_movestr

    def test_moves(self):
        test_data_file = r"tsumemi/test/test_cases_western_notation.txt"
        with open(test_data_file) as fh:
            for line1, line2, line3, _ in itertools.zip_longest(*[fh] * 4):
                (test_name, move, expected_movestr) = self._parse_move_test(
                    line1, line2, line3
                )
                movestr = self.move_writer.write_move(move, self.position)
                with self.subTest(msg=test_name, answer=expected_movestr):
                    self.assertEqual(expected_movestr, movestr)

    def test_drop(self):
        sfen = r"9/7+R1/sS1+p1+P2+R/2p+P1+P3/SS1n+pn3/9/9/9/3N5 b 2S2s 1"
        self.position.from_sfen(sfen)
        move = self.position.create_drop_move(Side.SENTE, KomaType.GI, Square.b84)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("S*84", movestr)

    def test_termination_move_mate(self):
        move = TerminationMove(GameTermination.MATE)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("MATE", movestr)


class TestJapaneseNotation(unittest.TestCase):
    def setUp(self):
        self.position = Position()
        self.move_writer = JapaneseMoveWriter()

    def _parse_move_test(self, line1, line2, line3):
        test_name = line1.rstrip()
        sfen = line2.rstrip()
        (start_coord, end_coord, promotion, expected_movestr) = line3.rstrip().split(
            " "
        )

        self.position.from_sfen(sfen)
        start_sq = Square.from_coord(int(start_coord))
        end_sq = Square.from_coord(int(end_coord))
        is_promotion = promotion == "+"
        move = self.position.create_move(start_sq, end_sq, is_promotion)
        return test_name, move, expected_movestr

    def test_moves(self):
        test_data_file = r"tsumemi/test/test_cases_japanese_notation.txt"
        with open(test_data_file, encoding="utf8") as fh:
            for line1, line2, line3, _ in itertools.zip_longest(*[iter(fh)] * 4):
                (test_name, move, expected_movestr) = self._parse_move_test(
                    line1, line2, line3
                )
                movestr = self.move_writer.write_move(move, self.position)
                with self.subTest(msg=test_name, answer=expected_movestr):
                    self.assertEqual(expected_movestr, movestr)

    def test_drop(self):
        sfen = r"9/7+R1/sS1+p1+P2+R/2p+P1+P3/SS1n+pn3/9/9/9/3N5 b 2S2s 1"
        self.position.from_sfen(sfen)
        move = self.position.create_drop_move(Side.SENTE, KomaType.GI, Square.b84)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("８四銀打", movestr)

    def test_termination_move_mate(self):
        move = TerminationMove(GameTermination.MATE)
        movestr = self.move_writer.write_move(move, self.position)
        self.assertEqual("詰み", movestr)
