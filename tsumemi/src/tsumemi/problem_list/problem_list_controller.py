from __future__ import annotations

import csv

from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.problem import Problem, ProblemStatus
from tsumemi.src.tsumemi.problem_list.problem_list_model import ProblemList
from tsumemi.src.tsumemi.problem_list.problem_list_view import ProblemListPane
from tsumemi.src.tsumemi.problem_list.problem_list_viewmodel import ProblemListViewModel

if TYPE_CHECKING:
    from collections.abc import Iterable
    import os
    import tkinter as tk
    import tsumemi.src.tsumemi.timer as timer

    PathLike = str | os.PathLike[str]


class ProblemListController:
    """Controller object for a problem list. Handles access to its
    underlying problem list (model).
    """

    def __init__(self) -> None:
        self.problem_list: ProblemList = ProblemList()
        self.viewmodel = ProblemListViewModel(self.problem_list)

    def go_next_problem(self) -> Problem | None:
        return self.problem_list.go_to_next()

    def go_prev_problem(self) -> Problem | None:
        return self.problem_list.go_to_prev()

    def go_to_problem(self, idx: int = 0) -> Problem | None:
        return self.problem_list.go_to_idx(idx)

    def set_status(self, status: ProblemStatus) -> None:
        self.problem_list.set_status(status)

    def set_time(self, time: timer.Time) -> None:
        self.problem_list.set_time(time)

    def clear_statuses(self) -> None:
        self.problem_list.clear_statuses()

    def clear_times(self) -> None:
        self.problem_list.clear_times()

    def make_problem_list_pane(self, parent: tk.Widget) -> ProblemListPane:
        problem_list_pane = ProblemListPane(parent, self.viewmodel)
        self.problem_list.add_observer(problem_list_pane.tvwfrm_problems)
        return problem_list_pane

    def set_problem_files(self, file_list: Iterable[PathLike]) -> Problem | None:
        self.problem_list.clear(suppress=True)
        self.problem_list.add_problems(
            (Problem(filepath) for filepath in file_list), suppress=True
        )
        self.problem_list.sort_by_file()
        return self.go_to_problem(0)

    def export_as_csv(self, filepath: PathLike) -> None:
        with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow(["filename", "status", "time (seconds)"])
            for prob in self.problem_list:
                prob_time = 0 if prob.time is None else prob.time.seconds
                csvwriter.writerow([prob.name, str(prob.status), prob_time])
