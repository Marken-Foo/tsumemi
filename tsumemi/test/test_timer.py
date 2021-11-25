import unittest

from time import sleep

from tsumemi.src.tsumemi import timer


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
            self.assertEqual(
                timer.Time.to_hms(timer.Time(case)),
                answer
            )
    
    def test_sec_to_str(self, places=1):
        cases = [0.0, 34.1, 78.2, 1437.0, 3602.6, 86400.0, 359999.9, 363659.7]
        answers = ["00:00:00.0", "00:00:34.1", "00:01:18.2", "00:23:57.0", "01:00:02.6", "24:00:00.0", "99:59:59.9", "101:00:59.7"]
        for case, answer in zip(cases, answers):
            self.assertEqual(
                timer.Time.to_hms_str(timer.Time(case), places=1),
                answer
            )