from __future__ import annotations

import re

from enum import Enum
from random import shuffle
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as event

if TYPE_CHECKING:
    import os
    from typing import Any, List, Optional, Union
    PathLike = Union[str, bytes, os.PathLike]


class ProblemStatus(Enum):
    NONE = 0; CORRECT = 1; WRONG = 2; SKIP = 3


class ProbListEvent(event.Event):
    def __init__(self, prob_list: List[Problem]) -> None:
        self.prob_list = prob_list
        return


class ProbStatusEvent(event.Event):
    def __init__(self, prob_idx: int, status: ProblemStatus) -> None:
        self.idx = prob_idx
        self.status = status
        return


class ProbTimeEvent(event.Event):
    def __init__(self, prob_idx: int, time: float) -> None:
        self.idx = prob_idx
        self.time = time
        return


class Problem:
    """Data class representing one tsume problem.
    """
    def __init__(self, filepath: PathLike) -> None:
        self.filepath: PathLike = filepath
        self.time: Optional[float] = None
        self.status: ProblemStatus = ProblemStatus.NONE
        return
    
    def get_filepath(self) -> PathLike:
        return self.filepath
    
    def __eq__(self, obj: Any) -> bool:
        # Used in tests, will be useful in future features
        return isinstance(obj, Problem) and self.filepath == obj.filepath


class ProblemList(event.Emitter):
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
    
    def __init__(self) -> None:
        self.problems: List[Problem] = []
        self.curr_prob: Optional[Problem] = None
        self.curr_prob_idx: Optional[int] = None
        self.observers: List[event.IObserver] = []
        return
    
    def clear(self, suppress=False) -> None:
        self.problems = []
        self.curr_prob = None
        self.curr_prob_idx = None
        if not suppress:
            self._notify_observers(ProbListEvent(self.problems))
        return
    
    def is_empty(self) -> bool:
        return not bool(self.problems)
    
    def add_problems(self, new_problems, suppress=False) -> None:
        self.problems.extend(new_problems)
        if not suppress:
            self._notify_observers(ProbListEvent(self.problems))
        return
    
    def get_curr_filepath(self) -> Optional[PathLike]:
        if self.curr_prob is None:
            return None
        else:
            return self.curr_prob.get_filepath()
    
    def set_status(self, status: ProblemStatus) -> None:
        if self.curr_prob is not None:
            self.curr_prob.status = status
            self._notify_observers(ProbStatusEvent(self.curr_prob_idx, status))
        return
    
    def set_time(self, time: float) -> None:
        if self.curr_prob is not None:
            self.curr_prob.time = time
            self._notify_observers(ProbTimeEvent(self.curr_prob_idx, time))
        return
    
    def next(self) -> bool:
        return (False if self.curr_prob_idx is None
            else self.go_to_idx(self.curr_prob_idx + 1))
    
    def prev(self) -> bool:
        return (False if self.curr_prob_idx is None
            else self.go_to_idx(self.curr_prob_idx - 1))
    
    def go_to_idx(self, idx: int) -> bool:
        """Change current problem to the one given by index. Return
        value indicates if current problem was successfully changed.
        """
        if idx is None or idx >= len(self.problems) or idx < 0:
            return False
        self.curr_prob = self.problems[idx]
        self.curr_prob_idx = idx
        return True
    
    def set_active_problem(self, prob) -> bool:
        if prob in self.problems:
            idx = self.problems.index(prob)
            self.curr_prob_idx = idx
            self.curr_prob = self.problems[self.curr_prob_idx]
            return True
        else:
            return False
    
    def sort(self, key, suppress=False) -> None:
        """Sort problem list in place, keeping focus on the same
        problem before and after the sort."""
        prob = self.curr_prob
        self.problems.sort(key=key)
        self.set_active_problem(prob)
        if not suppress:
            self._notify_observers(ProbListEvent(self.problems))
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
        z = list(zip(range(len(self.problems)), self.problems))
        shuffle(z)
        idxs, probs = zip(*z)
        self.problems = list(probs)
        self.curr_prob_idx = idxs.index(self.curr_prob_idx)
        curr_prob = self.problems[self.curr_prob_idx]
        self._notify_observers(ProbListEvent(self.problems))
        return