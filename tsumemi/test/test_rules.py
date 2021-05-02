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
        sfen = "p1p4P1/2P5P/3p3P1/3P4P/9/p4p3/1p3P3/p5p2/1p4P1P b - 1"
        # answer keys
        sente_moves = ["P18(19)", "P13(14)", "P13(14)+", "P11(12)+", "P22(23)", "P22(23)+", "P38(39)", "P46(47)", "P63(64)", "P63(64)+", "P71(72)+"]
        gote_moves = ["P39(38)+", "P47(46)", "P47(46)+", "P64(63)", "P72(71)", "P88(87)", "P88(87)+", "P92(91)", "P97(96)", "P97(96)+", "P99(98)+"]
        self.position.from_sfen(sfen)
        mvlist_sente = self.rules.generate_moves_fu(pos=self.position, side=Side.SENTE)
        mvlist_gote = self.rules.generate_moves_fu(pos=self.position, side=Side.GOTE)
        mvset_sente = set([move.to_latin() for move in mvlist_sente])
        mvset_gote = set([move.to_latin() for move in mvlist_gote])
        # check answers
        self.assertEqual(mvset_sente, set(sente_moves))
        self.assertEqual(mvset_gote, set(gote_moves))
    
    def test_lance_moves(self):
        sfen = "4p4/4L2P1/5L2l/6l2/9/7L1/5l2L/4l1p2/4P4 b - 1"
        # answer keys
        sente_moves = ["L16(17)", "L15(17)", "L14(17)", "L13(17)", "L13(17)+", "L25(26)", "L24(26)", "L23(26)", "L23(26)+", "L42(43)", "L42(43)+", "L41(43)+", "L51(52)+"]
        gote_moves = ["L14(13)", "L15(13)", "L16(13)", "L17(13)", "L17(13)+", "L35(34)", "L36(34)", "L37(34)", "L37(34)+", "L48(47)", "L48(47)+", "L49(47)+", "L59(58)+"]
        self.position.from_sfen(sfen)
        mvlist_sente = self.rules.generate_moves_ky(pos=self.position, side=Side.SENTE)
        mvlist_gote = self.rules.generate_moves_ky(pos=self.position, side=Side.GOTE)
        mvset_sente = set([move.to_latin() for move in mvlist_sente])
        mvset_gote = set([move.to_latin() for move in mvlist_gote])
        # check answers
        self.assertEqual(mvset_sente, set(sente_moves))
        self.assertEqual(mvset_gote, set(gote_moves))