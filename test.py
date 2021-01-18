import unittest

from io import StringIO
from time import sleep

from split_timer import SplitTimer
from kif_browser_gui import TimerPane
from kif_parser import KifReader, Piece


class TestTimer(unittest.TestCase):
    def setUp(self):
        self.timer = SplitTimer()
    
    def tearDown(self):
        self.timer = None
    
    def test_default_timer(self):
        self.assertFalse(self.timer.is_running)
        self.assertEqual(len(self.timer.lap_times), 0)
        self.assertEqual(self.timer.curr_lap_time, 0)
        self.assertIsNone(self.timer.start_time)
    
    def test_start_timer(self):
        self.timer.start()
        self.assertTrue(self.timer.is_running)
        self.assertIsNotNone(self.timer.start_time)
    
    def test_stop_timer(self):
        self.timer.start()
        self.timer.stop()
        self.assertFalse(self.timer.is_running)
        self.assertNotEqual(self.timer.curr_lap_time, 0)
    
    def test_stop_while_reset(self):
        self.timer.stop()
        self.assertFalse(self.timer.is_running)
        self.assertEqual(self.timer.curr_lap_time, 0)
    
    def test_split_while_run(self):
        duration = 0.1
        self.timer.start()
        sleep(duration)
        self.timer.split()
        self.assertTrue(self.timer.is_running)
        self.assertEqual(len(self.timer.lap_times), 1)
        self.assertAlmostEqual(self.timer.lap_times[0], duration, places=1)
        self.assertEqual(self.timer.curr_lap_time, 0)
        self.assertIsNotNone(self.timer.start_time)
    
    def test_split_while_reset(self):
        self.timer.split()
        self.assertFalse(self.timer.is_running)
        self.assertEqual(len(self.timer.lap_times), 0)
        self.assertEqual(self.timer.curr_lap_time, 0)
        self.assertIsNone(self.timer.start_time)
    
    def test_reset_while_stop(self):
        self.timer.start()
        self.timer.split()
        self.timer.stop()
        self.timer.reset()
        self.assertFalse(self.timer.is_running)
        self.assertEqual(len(self.timer.lap_times), 0)
        self.assertEqual(self.timer.curr_lap_time, 0)
        self.assertIsNone(self.timer.start_time)
    
    def test_reset_while_run(self):
        self.timer.start()
        self.timer.split()
        self.timer.reset()
        self.assertFalse(self.timer.is_running)
        self.assertEqual(len(self.timer.lap_times), 0)
        self.assertEqual(self.timer.curr_lap_time, 0)
        self.assertIsNone(self.timer.start_time)
    
    def test_read_while_reset(self):
        self.assertEqual(self.timer.read(), 0)
    
    def test_read_while_start(self):
        duration = 0.1
        self.timer.start()
        sleep(duration)
        self.assertAlmostEqual(self.timer.read(), duration, places=1)
    
    def test_read_while_stop(self):
        duration = 0.1
        self.timer.start()
        sleep(duration)
        self.timer.stop()
        self.assertAlmostEqual(self.timer.read(), duration, places=1)
    
    def test_multiple_split(self):
        duration = [0.1, 0.0, 0.2]
        self.timer.start()
        sleep(duration[0])
        self.timer.split()
        sleep(duration[1])
        self.timer.split()
        sleep(duration[2])
        self.timer.split()
        self.assertEqual(len(self.timer.lap_times), 3)
        for measured, waited in zip(self.timer.lap_times, duration):
            self.assertAlmostEqual(measured, waited, places=1)
    
    def test_get_split_times(self):
        laps = [13, 12, 17, 18]
        splits = [13, 25, 42, 60]
        self.timer.lap_times = laps
        for time, answer in zip(self.timer.get_split_times(), splits):
            self.assertEqual(time, answer)
    
    def test_sec_to_hms(self):
        cases = [0, 60, 61, 3600, 3601, 3660, 3662]
        answers = [(0,0,0), (0,1,0), (0,1,1), (1,0,0), (1,0,1), (1,1,0), (1,1,2)]
        for case, answer in zip(cases, answers):
            self.assertEqual(SplitTimer.sec_to_hms(case), answer)
    
    def test_sec_to_str(self, places=1):
        cases = [0.0, 34.1, 78.2, 1437.0, 3602.6, 86400.0, 359999.9, 363659.7]
        answers = ["00:00:00.0", "00:00:34.1", "00:01:18.2", "00:23:57.0", "01:00:02.6", "24:00:00.0", "99:59:59.9", "101:00:59.7"]
        for case, answer in zip(cases, answers):
            self.assertEqual(SplitTimer.sec_to_str(case, places=1), answer)


class TestTimerPane(unittest.TestCase):
    def setUp(self):
        class DummyCtrl():
            def __init__(self):
                self.split_timer = None
        self.ctrl = DummyCtrl()
        self.timer_pane = TimerPane(parent=None, controller=self.ctrl)
    
    def tearDown(self):
        self.ctrl = None
        self.timer_pane = None
    
    def test_reset(self):
        tt = TestTimer()
        tt.timer = self.timer_pane.timer
        tt.test_default_timer()


class TestKifReader(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()