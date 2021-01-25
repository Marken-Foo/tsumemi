import unittest

from io import StringIO
from time import sleep

import event
import timer

from kif_parser import KifReader, Piece
from model import Problem, ProblemList, ProblemStatus


class TestProblemList(unittest.TestCase):
    '''Tests for the internals of the ProblemList class.'''
    def setUp(self):
        def make_problem(name, time, status):
            prob = Problem(name)
            prob.time = time
            prob.status = status
            return prob
        
        def make_probs(names, times, statuses):
            probs = []
            for name, time, status in zip(names, times, statuses):
                probs.append(make_problem(name, time, status))
            return probs
        
        # make problem list with statuses, times and fake filepaths
        self.problem_list = ProblemList()
        names = [
            "1.kif", "2.kif", "3.kif", "4.kif", "5.kif", "6.kif", "7.kif", "8.kif"
        ]
        times = [11.1, 44.2, 13.3, 16.7, 65.0, 5.8, 9.1, 10.2]
        statuses = [
            ProblemStatus.CORRECT, ProblemStatus.SKIP, ProblemStatus.WRONG,
            ProblemStatus.SKIP, ProblemStatus.CORRECT, ProblemStatus.CORRECT,
            ProblemStatus.WRONG, ProblemStatus.WRONG
        ]
        self.problem_list.add_problems(make_probs(names, times, statuses))
        idx = 5
        self.problem_list.curr_prob_idx = idx
        self.problem_list.curr_prob = self.problem_list.problems[idx] # 6.kif
        # Register self as an Observer of the ProblemList
        self.problem_list.add_observer(self)
        self.event = None
        
        # Answer key to sortings
        # by file: good
        # by times: 67813425
        # by statuses: 15624378
        self.names_by_file = [
            "1.kif", "2.kif", "3.kif", "4.kif", "5.kif", "6.kif", "7.kif", "8.kif"
        ]
        self.names_by_time = [
            "6.kif", "7.kif", "8.kif", "1.kif", "3.kif", "4.kif", "2.kif", "5.kif"
        ]
        self.names_by_status = [
            "1.kif", "5.kif", "6.kif", "2.kif", "4.kif", "3.kif", "7.kif", "8.kif"
        ]
    
    def tearDown(self):
        self.problem_list = None
        self.event = None
    
    def on_notify(self, event):
        # to test Observer pattern, receive the Event
        self.event = event
    
    def verify_active_prob_by_idx(self, idx):
        self.assertEqual(idx, self.problem_list.curr_prob_idx)
        self.assertEqual(self.problem_list.problems[idx], self.problem_list.curr_prob)
    
    def verify_active_prob_by_prob(self, prob):
        self.assertEqual(prob, self.problem_list.curr_prob)
        self.assertEqual(self.problem_list.problems.index(prob), self.problem_list.curr_prob_idx)
    
    def verify_status_event(self):
        self.assertTrue(isinstance(self.event, event.ProbStatusEvent))
        self.assertEqual(self.event.status, self.problem_list.curr_prob.status)
    
    def verify_time_event(self):
        self.assertTrue(isinstance(self.event, event.ProbTimeEvent))
        self.assertEqual(self.event.time, self.problem_list.curr_prob.time)
    
    def verify_list_event(self):
        self.assertTrue(isinstance(self.event, event.ProbListEvent))
        self.assertEqual(self.event.prob_list, self.problem_list.problems)
    
    def test_clear(self):
        self.problem_list.clear()
        self.assertEqual(len(self.problem_list.problems), 0)
        self.assertIsNone(self.problem_list.curr_prob)
        self.assertIsNone(self.problem_list.curr_prob_idx)
    
    def test_notify_on_clear(self):
        self.problem_list.clear()
        self.verify_list_event()
    
    def test_add_one_problem(self):
        new_prob = Problem("new_problem.kif")
        self.problem_list.add_problems([new_prob])
        self.assertEqual(self.problem_list.problems[-1], new_prob)
    
    def test_add_three_problems(self):
        new_probs = [Problem("new1.kif"), Problem("new2.kif"), Problem("new3.kif")]
        self.problem_list.add_problems(new_probs)
        self.assertEqual(self.problem_list.problems[-1], new_probs[2])
        self.assertEqual(self.problem_list.problems[-2], new_probs[1])
        self.assertEqual(self.problem_list.problems[-3], new_probs[0])
    
    def test_notify_on_add(self):
        self.problem_list.add_problems([Problem("new.kif")])
        self.verify_list_event()
    
    def test_get_curr_filepath(self):
        self.assertEqual(self.problem_list.get_curr_filepath(), "6.kif")
    
    def test_get_curr_filepath_none(self):
        self.problem_list.clear()
        self.assertIsNone(self.problem_list.get_curr_filepath())
    
    def test_set_status_correct(self):
        self.problem_list.set_status(ProblemStatus.CORRECT)
        self.assertEqual(self.problem_list.curr_prob.status, ProblemStatus.CORRECT)
    
    def test_notify_set_status_correct(self):
        self.problem_list.set_status(ProblemStatus.CORRECT)
        self.verify_status_event()
    
    def test_set_status_wrong(self):
        self.problem_list.set_status(ProblemStatus.WRONG)
        self.assertEqual(self.problem_list.curr_prob.status, ProblemStatus.WRONG)
    
    def test_notify_set_status_wrong(self):
        self.problem_list.set_status(ProblemStatus.WRONG)
        self.verify_status_event()
    
    def test_set_time(self):
        time = 444.4
        self.problem_list.set_time(time)
        self.assertEqual(self.problem_list.curr_prob.time, time)
    
    def test_notify_set_time(self):
        time = 765.4
        self.problem_list.set_time(time)
        self.verify_time_event()
    
    def test_go_to_idx(self):
        target_idx = 4
        self.assertTrue(self.problem_list.go_to_idx(target_idx))
        self.verify_active_prob_by_idx(target_idx)
    
    def test_go_to_idx_out_of_range(self):
        init_idx = 3
        self.problem_list.go_to_idx(init_idx)
        target_idx = 798
        self.assertFalse(self.problem_list.go_to_idx(target_idx))
        self.verify_active_prob_by_idx(init_idx)
    
    def test_next_normal(self):
        idx = 5
        self.problem_list.go_to_idx(idx)
        self.assertTrue(self.problem_list.next())
        self.verify_active_prob_by_idx(idx+1)
    
    def test_next_at_end(self):
        end_idx = len(self.problem_list.problems) - 1
        self.problem_list.go_to_idx(end_idx)
        self.assertFalse(self.problem_list.next())
        self.verify_active_prob_by_idx(end_idx)
    
    def test_prev_normal(self):
        idx = 5
        self.problem_list.go_to_idx(idx)
        self.assertTrue(self.problem_list.prev())
        self.verify_active_prob_by_idx(idx-1)
    
    def test_prev_at_start(self):
        start_idx = 0
        self.problem_list.go_to_idx(start_idx)
        self.assertFalse(self.problem_list.prev())
        self.verify_active_prob_by_idx(start_idx)
    
    def test_sort_by_file(self):
        idx = 4
        self.problem_list.go_to_idx(idx)
        self.problem_list.sort_by_file()
        self.assertEqual([p.filepath for p in self.problem_list.problems], self.names_by_file)
        self.verify_active_prob_by_idx(idx)
    
    def test_sort_by_time(self):
        idx = 6
        self.problem_list.go_to_idx(idx)
        prob = self.problem_list.curr_prob
        self.problem_list.sort_by_time()
        self.assertEqual([p.filepath for p in self.problem_list.problems], self.names_by_time)
        self.verify_active_prob_by_prob(prob)
    
    def test_sort_by_status(self):
        idx = 2
        self.problem_list.go_to_idx(idx)
        prob = self.problem_list.curr_prob
        self.problem_list.sort_by_status()
        self.assertEqual([p.filepath for p in self.problem_list.problems], self.names_by_status)
        self.verify_active_prob_by_prob(prob)
    
    def test_notify_on_sort(self):
        self.problem_list.sort_by_file()
        self.verify_list_event()
        self.event = None
        self.problem_list.sort_by_status()
        self.verify_list_event()
        self.event = None
        self.problem_list.sort_by_time()
        self.verify_list_event()


class TestTimer(unittest.TestCase):
    '''Tests for the internals and interface of the SplitTimer class.'''
    def setUp(self):
        self.timer = timer.SplitTimer()
    
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
            self.assertEqual(timer.sec_to_hms(case), answer)
    
    def test_sec_to_str(self, places=1):
        cases = [0.0, 34.1, 78.2, 1437.0, 3602.6, 86400.0, 359999.9, 363659.7]
        answers = ["00:00:00.0", "00:00:34.1", "00:01:18.2", "00:23:57.0", "01:00:02.6", "24:00:00.0", "99:59:59.9", "101:00:59.7"]
        for case, answer in zip(cases, answers):
            self.assertEqual(timer.sec_to_str(case, places=1), answer)


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


if __name__ == "__main__":
    unittest.main()