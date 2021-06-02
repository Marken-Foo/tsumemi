from __future__ import annotations

import itertools
import math
import time

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as event

if TYPE_CHECKING:
    from typing import List, Iterator, Optional, Tuple


def sec_to_hms(seconds: float) -> Tuple[int, int, float]:
    """Take a time in seconds and return a tuple of
    (hours, minutes, seconds).
    """
    return (int(seconds // 3600), int((seconds % 3600) // 60), seconds % 60)


def _two_digits(num: float) -> str:
    """Take a float, make its integer part at least two chars long
    (clock display), and return it as a string.
    """
    return "0" + str(num) if num < 10 else str(num)


def sec_to_str(seconds: float, places: int = 1) -> str:
    hms = list(sec_to_hms(seconds))
    hms[2] = round(hms[2], places)
    return ":".join([_two_digits(i) for i in hms])


class TimerStartEvent(event.Event):
    pass


class TimerStopEvent(event.Event):
    pass


class TimerSplitEvent(event.Event):
    def __init__(self, lap_time: float) -> None:
        self.time: float = lap_time
        return


class SplitTimer:
    '''Class that works like a speedrunning split timer.
    Stores "lap times"; split times must be calculated from these.
    Split time = time elapsed since beginning.
    Lap time = time between splits.
    e.g. If I take splits at 0:30, 1:00, 1:30 and 2:00, I have 4 splits
    (those four), and 4 lap times (each lap is 30 seconds).
    '''
    
    def __init__(self) -> None:
        self.is_running: bool = False
        self.lap_times: List[float] = []
        # Elapsed (active) time since the start of this lap
        self.curr_lap_time: float = 0
        # Time at instant of last start() or split()
        self.start_time: Optional[float] = None
        return
    
    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            self.start_time = time.perf_counter()
        return
    
    def stop(self) -> None:
        if self.is_running:
            self.is_running = False
            if self.start_time is not None:
                self.curr_lap_time += time.perf_counter() - self.start_time
        return
    
    def split(self) -> Optional[float]:
        if self.start_time is None:
            # ill-defined operation
            return None
        if self.is_running:
            lap_time = (self.curr_lap_time + time.perf_counter()
                        - self.start_time)
            self.lap_times.append(lap_time)
            self.start_time = time.perf_counter()
            self.curr_lap_time = 0
            return lap_time
        else:
            # Splitting while the timer is paused "has no meaning".
            lap_time = self.curr_lap_time
            self.lap_times.append(lap_time)
            self.start_time = None
            self.curr_lap_time = 0
            return lap_time
    
    def reset(self) -> None:
        self.is_running = False
        self.lap_times = []
        self.curr_lap_time = 0
        self.start_time = None
        return
    
    def read(self) -> float:
        if self.start_time is None:
            return 0
        elif self.is_running:
            res = (math.fsum(self.lap_times)
                + self.curr_lap_time
                + time.perf_counter()
                - self.start_time
            )
        else:
            res = math.fsum(self.lap_times) + self.curr_lap_time
        return res
    
    def get_lap(self) -> Optional[float]:
        if self.lap_times:
            return self.lap_times[-1]
        else:
            return None
    
    def get_split_times(self) -> Iterator[float]:
        # Return a list of split times instead of lap times.
        return itertools.accumulate(self.lap_times)


class Timer(event.Emitter):
    """Wrapper for the SplitTimer class, with normal stopwatch
    functions. Emits events to be observed by GUI displays of
    the timer (or for other purposes)."""
    def __init__(self) -> None:
        self.clock = SplitTimer()
        self.observers: List[event.IObserver] = []
        return
    
    def read(self) -> float:
        return self.clock.read()
    
    def reset(self) -> None:
        self.clock.reset()
        self._notify_observers(TimerStopEvent())
        return
    
    def split(self) -> Optional[float]:
        time = self.clock.split()
        if time is not None:
            self._notify_observers(TimerSplitEvent(time))
        return time
    
    def start(self) -> None:
        self.clock.start()
        self._notify_observers(TimerStartEvent())
        return
    
    def stop(self) -> None:
        self.clock.stop()
        self._notify_observers(TimerStopEvent())
        return
    
    def toggle(self) -> None:
        if self.clock.is_running: # remove this private access
            self.stop()
        else:
            self.start()
        return