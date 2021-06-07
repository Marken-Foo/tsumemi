import unittest

import tsumemi.src.shogi.kif as kif
from tsumemi.src.shogi.kif import SFEN_FROM_HANDICAP, GameBuilderPVis, KifReader


def read_file(filename, reader, visitor):
    encodings = ["cp932", "utf-8"]
    for enc in encodings:
        try:
            with open(filename, "r", encoding=enc) as kif:
                reader.read(kif, visitor)
        except UnicodeDecodeError:
            pass
        else:
            break


class TestReadKifu(unittest.TestCase):
    def test_1(self):
        reader = KifReader()
        visitor = GameBuilderPVis()
        read_file(r"./tsumemi/test/test_kifus/1.kif", reader, visitor)
    
    def test_game(self):
        reader = KifReader()
        visitor = GameBuilderPVis()
        even_sfen = SFEN_FROM_HANDICAP["平手"]
        reader.game.position.from_sfen(even_sfen)
        self.assertEqual(reader.game.position.to_sfen(), even_sfen)
        sfen_test = reader.game.position.to_sfen()
        read_file(r"./tsumemi/test/test_kifus/testlinear.kifu", reader, visitor)
        # print(reader.game.position)
        sfen_answer = "+R3g1knl/3s2g2/p1p1pp1pp/3p5/9/1S5P1/P+sN1PPP1P/2+b2S1R1/LK5NL w B2GN4Plp 72"
        reader.game.go_to_end()
        self.assertEqual(reader.game.position.to_sfen(), sfen_answer)
        # print(reader.game.movetree.to_latin())
        # for i in range(1, 11, 1):
            # filename = r"./tsumemi/test/test_kifus/" + str(i) + ".kif"
            # read_file(filename, reader, GameBuilderPVis())
            # print(reader.game.position)
            # print(reader.game.position.to_sfen())
            # print(str(reader.game.movetree))
    
    def test_read_kif(self):
        reader = KifReader()
        read_file(r"./tsumemi/test/test_kifus/testlinear.kifu", reader, GameBuilderPVis())
        reference = reader.game
        reference.go_to_end()
        game = kif.read_kif(r"./tsumemi/test/test_kifus/testlinear.kifu")
        game.go_to_end()
        self.assertEqual(reference.position.to_sfen(), game.position.to_sfen())
    
    def test_branched(self):
        reader = KifReader()
        visitor = GameBuilderPVis()
        read_file(r"./tsumemi/test/test_kifus/branchedgame.kif", reader, visitor)
        # print(reader.game.position)
        # print(reader.game.movetree.to_latin())