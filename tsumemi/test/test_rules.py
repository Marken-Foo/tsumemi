import unittest

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side, Square
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
    
    def test_knight_moves(self):
        sfen = "N7N/4N1n2/9/5N3/n2n1N2N/3n5/9/2N1n4/n7n b - 1"
        # answer keys
        sente_moves = ["N23(15)", "N23(15)+", "N32(44)+", "N53(45)", "N53(45)+", "N33(45)", "N33(45)+", "N66(78)", "N86(78)"]
        gote_moves = ["N24(32)", "N44(32)", "N57(65)", "N57(65)+", "N77(65)", "N77(65)+", "N78(66)+", "N87(95)", "N87(95)+"]
        self.position.from_sfen(sfen)
        mvlist_sente = self.rules.generate_moves_ke(pos=self.position, side=Side.SENTE)
        mvlist_gote = self.rules.generate_moves_ke(pos=self.position, side=Side.GOTE)
        mvset_sente = set([move.to_latin() for move in mvlist_sente])
        mvset_gote = set([move.to_latin() for move in mvlist_gote])
        # check answers
        self.assertEqual(mvset_sente, set(sente_moves))
        self.assertEqual(mvset_gote, set(gote_moves))
    
    def test_silver_moves(self):
        sfen = "8S/7s1/7S1/6S2/9/6s2/7s1/7S1/8s b - 1"
        # answer keys
        sente_moves = ["S22(11)", "S22(11)+", "S22(23)", "S22(23)+", "S12(23)", "S12(23)+", "S32(23)", "S32(23)+", "S14(23)", "S14(23)+", "S33(34)", "S33(34)+", "S43(34)", "S43(34)+", "S25(34)", "S45(34)", "S17(28)", "S27(28)", "S37(28)", "S19(28)", "S39(28)"]
        gote_moves = ["S28(19)", "S28(19)+", "S28(27)", "S28(27)+", "S18(27)", "S18(27)+", "S38(27)", "S38(27)+", "S16(27)", "S16(27)+", "S37(36)", "S37(36)+", "S47(36)", "S47(36)+", "S25(36)", "S45(36)", "S13(22)", "S23(22)", "S33(22)", "S11(22)", "S31(22)"]
        self.position.from_sfen(sfen)
        mvlist_sente = self.rules.generate_moves_gi(pos=self.position, side=Side.SENTE)
        mvlist_gote = self.rules.generate_moves_gi(pos=self.position, side=Side.GOTE)
        mvset_sente = set([move.to_latin() for move in mvlist_sente])
        mvset_gote = set([move.to_latin() for move in mvlist_gote])
        # check answers
        self.assertEqual(mvset_sente, set(sente_moves))
        self.assertEqual(mvset_gote, set(gote_moves))
    
    def test_gold_moves(self):
        sfen = "8G/7G1/7g1/9/9/9/7G1/7g1/8g b - 1"
        # answer keys
        sente_moves = ["G12(11)", "G21(11)", "G31(22)", "G21(22)", "G32(22)", "G12(22)", "G23(22)", "G36(27)", "G26(27)", "G16(27)", "G37(27)", "G17(27)", "G28(27)"]
        gote_moves = ["G18(19)", "G29(19)", "G39(28)", "G29(28)", "G38(28)", "G18(28)", "G27(28)", "G34(23)", "G24(23)", "G14(23)", "G33(23)", "G13(23)", "G22(23)"]
        self.position.from_sfen(sfen)
        mvlist_sente = self.rules.generate_moves_ki(pos=self.position, side=Side.SENTE)
        mvlist_gote = self.rules.generate_moves_ki(pos=self.position, side=Side.GOTE)
        mvset_sente = set([move.to_latin() for move in mvlist_sente])
        mvset_gote = set([move.to_latin() for move in mvlist_gote])
        # check answers
        self.assertEqual(mvset_sente, set(sente_moves))
        self.assertEqual(mvset_gote, set(gote_moves))
    
    def test_bishop_moves(self):
        sfen = "9/7P1/9/5B3/9/3b5/9/1p7/9 b - 1"
        # answer keys
        sente_moves = ["B71(44)", "B71(44)+", "B62(44)", "B62(44)+", "B53(44)", "B53(44)+", "B33(44)", "B33(44)+", "B55(44)", "B66(44)", "B35(44)", "B26(44)", "B17(44)"]
        gote_moves = ["B39(66)", "B39(66)+", "B48(66)", "B48(66)+", "B57(66)", "B57(66)+", "B77(66)", "B77(66)+", "B55(66)", "B44(66)", "B75(66)", "B84(66)", "B93(66)"]
        self.position.from_sfen(sfen)
        mvlist_sente = self.rules.generate_moves_ka(pos=self.position, side=Side.SENTE)
        mvlist_gote = self.rules.generate_moves_ka(pos=self.position, side=Side.GOTE)
        mvset_sente = set([move.to_latin() for move in mvlist_sente])
        mvset_gote = set([move.to_latin() for move in mvlist_gote])
        # check answers
        self.assertEqual(mvset_sente, set(sente_moves))
        self.assertEqual(mvset_gote, set(gote_moves))
    
    def test_rook_moves(self):
        sfen = "9/3p5/9/9/2Pr1Rp2/9/9/5P3/9 b - 1"
        # answer keys
        sente_moves = ["R41(45)", "R41(45)+", "R42(45)", "R42(45)+", "R43(45)", "R43(45)+", "R44(45)", "R55(45)", "R65(45)", "R35(45)", "R46(45)", "R47(45)"]
        gote_moves = ["R69(65)", "R69(65)+", "R68(65)", "R68(65)+", "R67(65)", "R67(65)+", "R66(65)", "R55(65)", "R45(65)", "R75(65)", "R64(65)", "R63(65)"]
        self.position.from_sfen(sfen)
        mvlist_sente = self.rules.generate_moves_hi(pos=self.position, side=Side.SENTE)
        mvlist_gote = self.rules.generate_moves_hi(pos=self.position, side=Side.GOTE)
        mvset_sente = set([move.to_latin() for move in mvlist_sente])
        mvset_gote = set([move.to_latin() for move in mvlist_gote])
        # check answers
        self.assertEqual(mvset_sente, set(sente_moves))
        self.assertEqual(mvset_gote, set(gote_moves))
    
    def manual_test_drop_moves(self):
        # NOT automated test, needs manual verification
        sfen = "l1sgk1snl/6g2/p2ppp2p/2p6/9/9/P1SPPPP1P/2G6/LN2KGSNL b RBN3Prb3p 1"
        # answer keys
        self.position.from_sfen(sfen)
        droplist_fu = self.rules.generate_drop_moves(pos=self.position, side=Side.SENTE, ktype=KomaType.FU)
        droplist_ke = self.rules.generate_drop_moves(pos=self.position, side=Side.SENTE, ktype=KomaType.KE)
        droplist_ka = self.rules.generate_drop_moves(pos=self.position, side=Side.SENTE, ktype=KomaType.KA)
        # check answers
        # print([mv.to_latin() for mv in droplist_fu])
        # print([mv.to_latin() for mv in droplist_ke])
        # print([mv.to_latin() for mv in droplist_ka])