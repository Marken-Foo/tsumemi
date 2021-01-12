import time
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
    is_running = False
    lap_times = []
    # Elapsed (active) time since the start of this lap
    curr_lap_time = 0
    # Time at instant of last start() or split()
    start_time = None
    
    def __init__(self):
        return
    
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.perf_counter()
        return
    
    def stop(self):
        if self.is_running:
            self.is_running = False
            # this "is not None" if statement should be unnecessary - start_time should never be None once the timer starts running.
            if self.start_time is not None:
                self.curr_lap_time += time.perf_counter() - self.start_time
        return
    
    def split(self):
        if self.is_running:
            self.lap_times.append(self.curr_lap_time + time.perf_counter() - self.start_time)
            self.start_time = time.perf_counter()
            self.curr_lap_time = 0
        else:
            # why would you take a split when the timer is stopped? what meaning does that have?
            print("why would you do this?")
        return
    
    def reset(self):
        self.is_running = False
        self.lap_times = []
        self.curr_lap_time = 0
        self.start_time = None
        return
    
    def read(self):
        if self.is_running:
            return fsum(self.lap_times) + self.curr_lap_time + time.perf_counter() - self.start_time
        else:
            return fsum(self.lap_times) + self.curr_lap_time
    

if __name__ == "__main__":
    print("Hellomoto")
    timer = SplitTimer()
    timer.start()
    print(timer.read())
    print(timer.read())
    time.sleep(1)
    print(timer.read())
    timer.split()
    time.sleep(1)
    timer.split()
    time.sleep(1)
    timer.stop()
    timer.split()
    print(timer.lap_times)
    print(timer.read())