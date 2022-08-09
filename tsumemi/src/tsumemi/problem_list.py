from __future__ import annotations

import operator
import random
import re

from enum import Enum
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.timer as timer

if TYPE_CHECKING:
    import os
    from typing import Any, Iterable, List, Optional, Union
    PathLike = Union[str, os.PathLike]


class ProblemStatus(Enum):
    NONE = 0; CORRECT = 1; WRONG = 2; SKIP = 3
    
    def __str__(self):
        return self.name


class ProbSelectedEvent(evt.Event):
    def __init__(self, sender: ProblemList, prob: Problem) -> None:
        self.sender = sender
        self.problem = prob
        return


class ProbListEvent(evt.Event):
    def __init__(self, sender: ProblemList) -> None:
        self.sender = sender
        return


class ProbStatusEvent(evt.Event):
    def __init__(self, prob_idx: int, status: ProblemStatus) -> None:
        self.idx = prob_idx
        self.status = status
        return


class ProbTimeEvent(evt.Event):
    def __init__(self, prob_idx: int, time: timer.Time) -> None:
        self.idx = prob_idx
        self.time = time
        return


class Problem:
    """Data class representing one tsume problem.
    """
    def __init__(self, filepath: PathLike) -> None:
        self.filepath: PathLike = filepath
        self.time: Optional[timer.Time] = None
        self.status: ProblemStatus = ProblemStatus.NONE
        return
    
    def __eq__(self, obj: Any) -> bool:
        # Used in tests, will be useful in future features
        return isinstance(obj, Problem) and self.filepath == obj.filepath


class ProblemList(evt.Emitter):
    """Represent a sortable list of problems with a "pointer" to the
    current active problem. Also stores metadata about problem like
    solve time and status.
    """
    @staticmethod
    def natural_sort_key(str: str, _nsre=re.compile(r'(\d+)')
        ) -> List[Union[int, str]]:
        return [int(c) if c.isdigit() else c.lower() for c in _nsre.split(str)]
    
    @staticmethod
    def _file_key(prob) -> List[Union[int, str]]:
        return ProblemList.natural_sort_key(prob.filepath)
    
    def __init__(self, problems: Optional[List[Problem]] = None) -> None:
        super().__init__()
        self.problems: List[Problem] = [] if problems is None else problems
        self.curr_prob: Optional[Problem] = None
        self.curr_prob_idx: Optional[int] = None
        return
    
    def __iter__(self):
        return self.problems.__iter__()
    
    def __len__(self):
        return len(self.problems)
    
    def clear(self, suppress=False) -> None:
        self.problems = []
        self.curr_prob = None
        self.curr_prob_idx = None
        if not suppress:
            self._notify_observers(ProbListEvent(self))
        return
    
    def clear_statuses(self, suppress=False) -> None:
        for prob in self.problems:
            prob.status = ProblemStatus.NONE
        if not suppress:
            self._notify_observers(ProbListEvent(self))
        return
    
    def clear_times(self, suppress=False) -> None:
        for prob in self.problems:
            prob.time = None
        if not suppress:
            self._notify_observers(ProbListEvent(self))
        return
    
    def is_empty(self) -> bool:
        return not bool(self.problems)
    
    def add_problem(self, new_problem: Problem,
            suppress: bool = False
        ) -> None:
        self.problems.append(new_problem)
        if not suppress:
            self._notify_observers(ProbListEvent(self))
        return
    
    def add_problems(self, new_problems: Iterable[Problem],
            suppress: bool = False
        ) -> None:
        self.problems.extend(new_problems)
        if not suppress:
            self._notify_observers(ProbListEvent(self))
        return
    
    #=== Getters/queries
    def get_curr_filepath(self) -> Optional[PathLike]:
        if self.curr_prob is None:
            return None
        else:
            return self.curr_prob.filepath
    
    def filter_by_status(self, *args: ProblemStatus) -> ProblemList:
        return ProblemList([
            prob for prob in self.problems if (prob.status in args)
        ])
    
    def get_total_time(self) -> timer.Time:
        return sum(
            (prob.time for prob in self.problems if (prob.time is not None)),
            start=timer.Time(0)
        )
    
    def get_slowest_problem(self) -> Optional[Problem]:
        return max(
            (prob for prob in self.problems if (prob.time is not None)),
            key=operator.attrgetter("time"),
            default=None,
        )
    
    def get_fastest_problem(self) -> Optional[Problem]:
        return min(
            (prob for prob in self.problems if (prob.time is not None)),
            key=operator.attrgetter("time"),
            default=None,
        )
    
    #=== Setting methods
    def set_status(self, status: ProblemStatus) -> None:
        if self.curr_prob is not None:
            assert self.curr_prob_idx is not None # for mypy
            self.curr_prob.status = status
            self._notify_observers(ProbStatusEvent(self.curr_prob_idx, status))
        return
    
    def set_time(self, time: timer.Time) -> None:
        if self.curr_prob is not None:
            assert self.curr_prob_idx is not None # for mypy
            self.curr_prob.time = time
            self._notify_observers(ProbTimeEvent(self.curr_prob_idx, time))
        return
    
    #=== Navigation methods
    def go_to_idx(self, idx: int) -> Optional[Problem]:
        """Go to the problem at the given index and return it.
        """
        if idx >= len(self.problems) or idx < 0:
            return None
        prob = self.problems[idx]
        self.curr_prob = prob
        self.curr_prob_idx = idx
        self._notify_observers(ProbSelectedEvent(sender=self, prob=prob))
        return self.curr_prob
    
    def go_to_next(self) -> Optional[Problem]:
        return (None if self.curr_prob_idx is None
            else self.go_to_idx(self.curr_prob_idx + 1))
    
    def go_to_prev(self) -> Optional[Problem]:
        return (None if self.curr_prob_idx is None
            else self.go_to_idx(self.curr_prob_idx - 1))
    
    #=== Sorting methods
    def sort(self, key, suppress=False) -> None:
        """Sort problem list in place, keeping focus on the same
        problem before and after the sort."""
        old_prob = self.curr_prob
        self.problems.sort(key=key)
        self._set_active_problem(old_prob)
        if not suppress:
            self._notify_observers(ProbListEvent(self))
        return
    
    def sort_by_file(self) -> None:
        return self.sort(key=ProblemList._file_key)
    
    def sort_by_time(self) -> None:
        return self.sort(key=lambda p: -1.0 if p.time is None else p.time)
    
    def sort_by_status(self) -> None:
        return self.sort(key=lambda p: p.status.name)
    
    def randomise(self) -> None:
        """Randomly shuffle problem list in place, keeping focus on
        the same problem before and after the shuffle.
        """
        z = list(enumerate(self.problems))
        random.shuffle(z)
        idxs, probs = zip(*z)
        self.problems = list(probs)
        self.curr_prob_idx = idxs.index(self.curr_prob_idx)
        curr_prob = self.problems[self.curr_prob_idx]
        self._notify_observers(ProbListEvent(self))
        return
    
    def _set_active_problem(self, prob) -> bool:
        if prob in self.problems:
            idx = self.problems.index(prob)
            self.curr_prob_idx = idx
            self.curr_prob = self.problems[self.curr_prob_idx]
            return True
        else:
            return False
