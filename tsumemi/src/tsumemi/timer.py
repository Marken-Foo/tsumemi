from __future__ import annotations

import itertools
import math
import time

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt

if TYPE_CHECKING:
    from typing import Any, Iterator, List, Optional, Tuple


def _two_digits(num: float) -> str:
    """Take a float, make its integer part at least two chars long
    (clock display), and return it as a string.
    """
    return "0" + str(num) if num < 10 else str(num)


class Time:
    def __init__(self, time_: float) -> None:
        self.seconds: float = time_
        return

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Time):
            return self.seconds == other.seconds
        raise TypeError(f"Types Time and {type(other)} cannot be compared")

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Time):
            return self.seconds > other.seconds
        raise TypeError(f"Types Time and {type(other)} cannot be compared")

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Time):
            return self.seconds < other.seconds
        raise TypeError(f"Types Time and {type(other)} cannot be compared")

    def __ge__(self, other: Any) -> bool:
        return self.__gt__(other) or self.__eq__(other)

    def __le__(self, other: Any) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def __add__(self, other: Any) -> Time:
        if isinstance(other, Time):
            return Time(self.seconds + other.seconds)
        raise TypeError(f"Types Time and {type(other)} cannot be added")

    def __radd__(self, other: Any) -> Time:
        return self.__add__(other)

    def __str__(self) -> str:
        return self.to_hms_str()

    def to_hms(self) -> Tuple[int, int, float]:
        hours = int(self.seconds // 3600)
        minutes = int((self.seconds % 3600) // 60)
        seconds = self.seconds % 60
        return (hours, minutes, seconds)

    def to_hms_str(self, places: int = 1) -> str:
        hms = list(self.to_hms())
        hms[2] = round(hms[2], places)
        return ":".join([_two_digits(i) for i in hms])


class TimerEvent(evt.Event):
    def __init__(self, clock: Timer) -> None:
        evt.Event.__init__(self)
        self.clock: Timer = clock
        return


class TimerStartEvent(TimerEvent):
    pass


class TimerStopEvent(TimerEvent):
    pass


class TimerSplitEvent(TimerEvent):
    def __init__(self, clock: Timer, lap_time: Time) -> None:
        TimerEvent.__init__(self, clock)
        self.time: Time = lap_time
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
            lap_time = (self.curr_lap_time
                + time.perf_counter() - self.start_time
            )
            self.lap_times.append(lap_time)
            self.start_time = time.perf_counter()
            self.curr_lap_time = 0
            return lap_time
        else:
            # Splitting while the timer is paused "has no meaning".
            lap_time = self.curr_lap_time
            self.lap_times.append(lap_time)
            self.start_time = self.read()
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


class Timer(evt.Emitter):
    """Wrapper for the SplitTimer class, with normal stopwatch
    functions. Emits events to be observed by GUI displays of
    the timer (or for other purposes)."""
    def __init__(self) -> None:
        evt.Emitter.__init__(self)
        self.clock = SplitTimer()
        return

    def read(self) -> Time:
        return Time(self.clock.read())

    def reset(self) -> None:
        self.clock.reset()
        self._notify_observers(TimerStopEvent(self))
        return

    def split(self) -> Optional[Time]:
        reading: Optional[float] = self.clock.split()
        if reading is not None:
            time_ = Time(reading)
            self._notify_observers(TimerSplitEvent(self, time_))
            return time_
        return None

    def start(self) -> None:
        self.clock.start()
        self._notify_observers(TimerStartEvent(self))
        return

    def stop(self) -> None:
        self.clock.stop()
        self._notify_observers(TimerStopEvent(self))
        return

    def toggle(self) -> None:
        if self.clock.is_running: # remove this private access
            self.stop()
        else:
            self.start()
        return
