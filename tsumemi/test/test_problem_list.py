import unittest

import tsumemi.src.tsumemi.problem_list.problem_list_model as plist


class TestProblemList(unittest.TestCase):
    '''Tests for the internals of the ProblemList class.'''
    def setUp(self):
        def make_problem(name, time, status):
            prob = plist.Problem(name)
            prob.time = time
            prob.status = status
            return prob
        
        def make_probs(names, times, statuses):
            probs = []
            for name, time, status in zip(names, times, statuses):
                probs.append(make_problem(name, time, status))
            return probs
        
        # make problem list with statuses, times and fake filepaths
        self.problem_list = plist.ProblemList()
        names = [
            "1.kif", "2.kif", "3.kif", "4.kif", "5.kif", "6.kif", "7.kif", "8.kif"
        ]
        times = [11.1, 44.2, 13.3, 16.7, 65.0, 5.8, 9.1, 10.2]
        statuses = [
            plist.ProblemStatus.CORRECT, plist.ProblemStatus.SKIP,
            plist.ProblemStatus.WRONG, plist.ProblemStatus.SKIP,
            plist.ProblemStatus.CORRECT, plist.ProblemStatus.CORRECT,
            plist.ProblemStatus.WRONG, plist.ProblemStatus.WRONG
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
        self.assertTrue(isinstance(self.event, plist.ProbStatusEvent))
        self.assertEqual(self.event.status, self.problem_list.curr_prob.status)
    
    def verify_time_event(self):
        self.assertTrue(isinstance(self.event, plist.ProbTimeEvent))
        self.assertEqual(self.event.time, self.problem_list.curr_prob.time)
    
    def verify_list_event(self):
        self.assertTrue(isinstance(self.event, plist.ProbListEvent))
        self.assertEqual(self.event.sender, self.problem_list)
    
    def test_clear(self):
        self.problem_list.clear()
        self.assertEqual(len(self.problem_list.problems), 0)
        self.assertIsNone(self.problem_list.curr_prob)
        self.assertIsNone(self.problem_list.curr_prob_idx)
    
    def test_notify_on_clear(self):
        self.problem_list.clear()
        self.verify_list_event()
    
    def test_add_one_problem(self):
        new_prob = plist.Problem("new_problem.kif")
        self.problem_list.add_problems([new_prob])
        self.assertEqual(self.problem_list.problems[-1], new_prob)
    
    def test_add_three_problems(self):
        new_probs = [
            plist.Problem("new1.kif"),
            plist.Problem("new2.kif"),
            plist.Problem("new3.kif"),
        ]
        self.problem_list.add_problems(new_probs)
        self.assertEqual(self.problem_list.problems[-1], new_probs[2])
        self.assertEqual(self.problem_list.problems[-2], new_probs[1])
        self.assertEqual(self.problem_list.problems[-3], new_probs[0])
    
    def test_notify_on_add(self):
        self.problem_list.add_problems([plist.Problem("new.kif")])
        self.verify_list_event()
    
    def test_get_curr_filepath(self):
        self.assertEqual(self.problem_list.get_curr_filepath(), "6.kif")
    
    def test_get_curr_filepath_none(self):
        self.problem_list.clear()
        self.assertIsNone(self.problem_list.get_curr_filepath())
    
    def test_set_status_correct(self):
        self.problem_list.set_status(plist.ProblemStatus.CORRECT)
        self.assertEqual(
            self.problem_list.curr_prob.status,
            plist.ProblemStatus.CORRECT
        )
    
    def test_notify_set_status_correct(self):
        self.problem_list.set_status(plist.ProblemStatus.CORRECT)
        self.verify_status_event()
    
    def test_set_status_wrong(self):
        self.problem_list.set_status(plist.ProblemStatus.WRONG)
        self.assertEqual(
            self.problem_list.curr_prob.status,
            plist.ProblemStatus.WRONG
        )
    
    def test_notify_set_status_wrong(self):
        self.problem_list.set_status(plist.ProblemStatus.WRONG)
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
        self.assertTrue(self.problem_list.go_to_next())
        self.verify_active_prob_by_idx(idx+1)
    
    def test_next_at_end(self):
        end_idx = len(self.problem_list.problems) - 1
        self.problem_list.go_to_idx(end_idx)
        self.assertFalse(self.problem_list.go_to_next())
        self.verify_active_prob_by_idx(end_idx)
    
    def test_prev_normal(self):
        idx = 5
        self.problem_list.go_to_idx(idx)
        self.assertTrue(self.problem_list.go_to_prev())
        self.verify_active_prob_by_idx(idx-1)
    
    def test_prev_at_start(self):
        start_idx = 0
        self.problem_list.go_to_idx(start_idx)
        self.assertFalse(self.problem_list.go_to_prev())
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