import time

from itertools import accumulate
from math import fsum

class SplitTimer:
    '''
    Split timer class. Works like a speedrunning split timer.
    Stores "lap times", and split times must be calculated from these.
    Split time = time elapsed since beginning, lap time = time between splits.
    e.g. If I take splits at 0:30, 1:00, 1:30 and 2:00,
    I have 4 splits (those four), and 4 lap times (each lap is 30 seconds).
    The logic for this class is vaguely "state-based", if that helps.
    '''
    
    def __init__(self):
        self.is_running = False
        self.lap_times = []
        # Elapsed (active) time since the start of this lap
        self.curr_lap_time = 0
        # Time at instant of last start() or split()
        self.start_time = None
        return
    
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.perf_counter()
        return
    
    def stop(self):
        if self.is_running:
            self.is_running = False
            if self.start_time is not None:
                self.curr_lap_time += time.perf_counter() - self.start_time
        return
    
    def split(self):
        if self.start_time is None:
            # ill-defined operation
            return
        if self.is_running:
            self.lap_times.append(self.curr_lap_time + time.perf_counter() - self.start_time)
            self.start_time = time.perf_counter()
            self.curr_lap_time = 0
        else:
            # Taking a split while the timer is paused "has no meaning".
            # But we implement it anyway.
            self.lap_times.append(self.curr_lap_time)
            self.start_time = None
            self.curr_lap_time = 0
        return
    
    def reset(self):
        self.is_running = False
        self.lap_times = []
        self.curr_lap_time = 0
        self.start_time = None
        return
    
    def read(self):
        if self.is_running:
            res = fsum(self.lap_times) + self.curr_lap_time + time.perf_counter() - self.start_time
        else:
            res = fsum(self.lap_times) + self.curr_lap_time
        return res
    
    def get_split_times(self):
        # Return a list of split times instead of lap times.
        return accumulate(self.lap_times)
    
    @staticmethod
    def sec_to_hms(seconds):
        # Take time in seconds, return tuple of (hours, minutes, seconds).
        return (int(seconds // 3600), int((seconds % 3600) // 60), seconds % 60)
    
    @staticmethod
    def _two_digits(num):
        # Take num, make integer part two chars (clock display), return string
        if num < 10:
            return "0" + str(num)
        else:
            return str(num)
    
    @staticmethod
    def sec_to_str(seconds, places=1):
        hms = list(SplitTimer.sec_to_hms(seconds))
        hms[2] = round(hms[2], places)
        return ":".join([SplitTimer._two_digits(i) for i in hms])