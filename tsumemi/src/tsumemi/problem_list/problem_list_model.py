from __future__ import annotations

import operator
import random
import re

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt

from tsumemi.src.tsumemi import timer
from tsumemi.src.tsumemi.problem import Problem, ProblemStatus

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from os import PathLike
    from typing import Any


class ProbSelectedEvent(evt.Event):
    def __init__(self, sender: ProblemList, prob: Problem) -> None:
        evt.Event.__init__(self)
        self.sender = sender
        self.problem = prob


class ProbListEvent(evt.Event):
    def __init__(self, sender: ProblemList) -> None:
        evt.Event.__init__(self)
        self.sender = sender


class ProbStatusEvent(evt.Event):
    def __init__(self, prob_idx: int, status: ProblemStatus) -> None:
        evt.Event.__init__(self)
        self.idx = prob_idx
        self.status = status


class ProbTimeEvent(evt.Event):
    def __init__(self, prob_idx: int, time: timer.Time) -> None:
        evt.Event.__init__(self)
        self.idx = prob_idx
        self.time = time


class ProblemList(evt.Emitter):
    """Represent a sortable list of problems with a "pointer" to the
    current active problem. Also stores metadata about problem like
    solve time and status.
    """

    @staticmethod
    def natural_sort_key(
        _str: str, _nsre: re.Pattern[str] = re.compile(r"(\d+)")
    ) -> list[int | str]:
        return [int(c) if c.isdigit() else c.lower() for c in _nsre.split(_str)]

    @staticmethod
    def _file_key(prob: Problem) -> list[int | str]:
        return ProblemList.natural_sort_key(str(prob.filepath))

    def __init__(self, problems: list[Problem] | None = None) -> None:
        evt.Emitter.__init__(self)
        self.problems: list[Problem] = [] if problems is None else problems
        self.curr_prob: Problem | None = None
        self.curr_prob_idx: int | None = None

    def __iter__(self) -> Iterator[Problem]:
        return self.problems.__iter__()

    def __len__(self) -> int:
        return len(self.problems)

    def clear(self, suppress: bool = False) -> None:
        self.problems = []
        self.curr_prob = None
        self.curr_prob_idx = None
        if not suppress:
            self._notify_observers(ProbListEvent(self))

    def clear_statuses(self, suppress: bool = False) -> None:
        for prob in self.problems:
            prob.status = ProblemStatus.NONE
        if not suppress:
            self._notify_observers(ProbListEvent(self))

    def clear_times(self, suppress: bool = False) -> None:
        for prob in self.problems:
            prob.time = None
        if not suppress:
            self._notify_observers(ProbListEvent(self))

    def is_empty(self) -> bool:
        return not bool(self.problems)

    def add_problem(self, new_problem: Problem, suppress: bool = False) -> None:
        self.problems.append(new_problem)
        if not suppress:
            self._notify_observers(ProbListEvent(self))

    def add_problems(
        self, new_problems: Iterable[Problem], suppress: bool = False
    ) -> None:
        self.problems.extend(new_problems)
        if not suppress:
            self._notify_observers(ProbListEvent(self))

    # === Getters/queries
    def get_curr_filepath(self) -> PathLike[str] | None:
        if self.curr_prob is None:
            return None
        else:
            return self.curr_prob.filepath

    def filter_by_status(self, *args: ProblemStatus) -> ProblemList:
        return ProblemList([prob for prob in self.problems if (prob.status in args)])

    def get_total_time(self) -> timer.Time:
        return sum(
            (prob.time for prob in self.problems if prob.time is not None),
            start=timer.Time(0),
        )

    def get_slowest_problem(self) -> Problem | None:
        return max(
            (prob for prob in self.problems if prob.time is not None),
            key=operator.attrgetter("time"),
            default=None,
        )

    def get_fastest_problem(self) -> Problem | None:
        return min(
            (prob for prob in self.problems if prob.time is not None),
            key=operator.attrgetter("time"),
            default=None,
        )

    # === Setting methods
    def set_status(self, status: ProblemStatus) -> None:
        if self.curr_prob is not None:
            assert self.curr_prob_idx is not None  # for mypy
            self.curr_prob.status = status
            self._notify_observers(ProbStatusEvent(self.curr_prob_idx, status))

    def set_time(self, time: timer.Time) -> None:
        if self.curr_prob is not None:
            assert self.curr_prob_idx is not None  # for mypy
            self.curr_prob.time = time
            self._notify_observers(ProbTimeEvent(self.curr_prob_idx, time))

    # === Navigation methods
    def go_to_idx(self, idx: int) -> Problem | None:
        """Go to the problem at the given index and return it."""
        if idx >= len(self.problems) or idx < 0:
            return None
        prob = self.problems[idx]
        self.curr_prob = prob
        self.curr_prob_idx = idx
        self._notify_observers(ProbSelectedEvent(sender=self, prob=prob))
        return self.curr_prob

    def go_to_next(self) -> Problem | None:
        return (
            None
            if self.curr_prob_idx is None
            else self.go_to_idx(self.curr_prob_idx + 1)
        )

    def go_to_prev(self) -> Problem | None:
        return (
            None
            if self.curr_prob_idx is None
            else self.go_to_idx(self.curr_prob_idx - 1)
        )

    # === Sorting methods
    def sort(self, key: Callable[[Problem], Any], suppress: bool = False) -> None:
        """Sort problem list in place, keeping focus on the same
        problem before and after the sort."""
        old_prob = self.curr_prob
        self.problems.sort(key=key)
        self._set_active_problem(old_prob)
        if not suppress:
            self._notify_observers(ProbListEvent(self))

    def sort_by_file(self) -> None:
        return self.sort(key=ProblemList._file_key)

    def sort_by_time(self) -> None:
        return self.sort(key=lambda p: timer.Time(-1.0) if p.time is None else p.time)

    def sort_by_status(self) -> None:
        return self.sort(key=lambda p: p.status.name)

    def randomise(self) -> None:
        """Randomly shuffle problem list in place, keeping focus on
        the same problem before and after the shuffle.
        """
        idxed_problems = list(enumerate(self.problems))
        random.shuffle(idxed_problems)
        idxs, probs = zip(*idxed_problems)
        self.problems = list(probs)
        self.curr_prob_idx = idxs.index(self.curr_prob_idx)
        self._notify_observers(ProbListEvent(self))

    def _set_active_problem(self, prob: Problem | None) -> bool:
        if prob is None:
            self.curr_prob = None
            return True
        if prob not in self.problems:
            return False
        idx = self.problems.index(prob)
        self.curr_prob_idx = idx
        self.curr_prob = self.problems[self.curr_prob_idx]
        return True
