from __future__ import annotations

import operator
from typing import TYPE_CHECKING
from tsumemi.src.tsumemi import timer
from tsumemi.src.tsumemi.problem import ProblemStatus

if TYPE_CHECKING:
    from collections.abc import Generator
    from tsumemi.src.tsumemi.problem import Problem
    from tsumemi.src.tsumemi.problem_list.problem_list_model import ProblemList


def filter_by_status(
    problem_list: ProblemList, *args: ProblemStatus
) -> Generator[Problem]:
    return (p for p in problem_list if (p.status in args))


def get_num_total(problem_list: ProblemList) -> int:
    return len(problem_list)


def get_num_correct(problem_list: ProblemList) -> int:
    return len(list(filter_by_status(problem_list, ProblemStatus.CORRECT)))


def get_num_wrong(problem_list: ProblemList) -> int:
    return len(list(filter_by_status(problem_list, ProblemStatus.WRONG)))


def get_num_skipped(problem_list: ProblemList) -> int:
    return len(list(filter_by_status(problem_list, ProblemStatus.SKIP)))


def get_total_time(problem_list: ProblemList) -> timer.Time:
    problems = filter_by_status(
        problem_list,
        ProblemStatus.CORRECT,
        ProblemStatus.WRONG,
        ProblemStatus.SKIP,
    )
    return sum((p.time for p in problems if p.time is not None), start=timer.Time(0))


def get_fastest_problem(problem_list: ProblemList) -> Problem | None:
    return min(
        (p for p in problem_list if p.time is not None),
        key=operator.attrgetter("time"),
        default=None,
    )


def get_slowest_problem(problem_list: ProblemList) -> Problem | None:
    return max(
        (p for p in problem_list if p.time is not None),
        key=operator.attrgetter("time"),
        default=None,
    )
