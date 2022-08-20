from __future__ import annotations

import csv
import os

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.problem_list.problem_list_model as plist

from tsumemi.src.tsumemi.problem_list.problem_list_view import ProblemListPane
from tsumemi.src.tsumemi.problem_list.problem_list_viewmodel import ProblemListViewModel

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Iterable, Optional, Union
    import tsumemi.src.tsumemi.timer as timer
    PathLike = Union[str, os.PathLike]


class ProblemListController:
    """Controller object for a problem list. Handles access to its
    underlying problem list (model).
    """
    def __init__(self) -> None:
        self.problem_list: plist.ProblemList = plist.ProblemList()
        self.directory: Optional[PathLike] = None
        self.viewmodel = ProblemListViewModel(self.problem_list)
        return

    def go_next_problem(self) -> Optional[plist.Problem]:
        return self.problem_list.go_to_next()

    def go_prev_problem(self) -> Optional[plist.Problem]:
        return self.problem_list.go_to_prev()

    def go_to_problem(self, idx: int = 0) -> Optional[plist.Problem]:
        return self.problem_list.go_to_idx(idx)

    def set_status(self, status: plist.ProblemStatus) -> None:
        self.problem_list.set_status(status)
        return

    def set_time(self, time: timer.Time) -> None:
        self.problem_list.set_time(time)
        return

    def clear_statuses(self) -> None:
        self.problem_list.clear_statuses()
        return

    def clear_times(self) -> None:
        self.problem_list.clear_times()
        return

    def make_problem_list_pane(self, parent: tk.Widget) -> ProblemListPane:
        problem_list_pane = ProblemListPane(parent, self.viewmodel)
        self.problem_list.add_observer(problem_list_pane.tvwfrm_problems)
        return problem_list_pane

    def set_directory(self,
            directory: PathLike,
            file_list: Iterable[PathLike],
        ) -> Optional[plist.Problem]:
        """Open directory and set own problem list to contents.
        """
        self.problem_list.clear(suppress=True)
        self.problem_list.add_problems(
            (plist.Problem(filepath) for filepath in file_list),
            suppress=True
        )
        self.problem_list.sort_by_file()
        self.directory = directory
        return self.go_to_problem(0)

    def generate_statistics(self) -> ProblemListStats:
        return ProblemListStats(self.problem_list,
            self.directory if self.directory else ""
        )

    def export_as_csv(self, filepath: PathLike) -> None:
        with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow(["filename", "status", "time (seconds)"])
            for prob in self.problem_list:
                prob_filename = os.path.basename(
                    os.path.normpath(prob.filepath)
                )
                prob_status = str(prob.status)
                prob_time = 0 if prob.time is None else prob.time.seconds
                csvwriter.writerow([prob_filename, prob_status, prob_time])
        return


class ProblemListStats:
    """A helper object that can be queried for the solving statistics
    of the problems inside the problem list it refers to.
    """
    def __init__(self,
            problem_list: plist.ProblemList,
            directory: PathLike = ""
        ) -> None:
        self.problem_list: plist.ProblemList = problem_list
        self.directory: str = str(os.path.basename(os.path.normpath(directory)))
        return

    def get_num_total(self) -> int:
        return len(self.problem_list)

    def get_num_correct(self) -> int:
        return len(
            self.problem_list.filter_by_status(plist.ProblemStatus.CORRECT)
        )

    def get_num_wrong(self) -> int:
        return len(
            self.problem_list.filter_by_status(plist.ProblemStatus.WRONG)
        )

    def get_num_skip(self) -> int:
        return len(
            self.problem_list.filter_by_status(plist.ProblemStatus.SKIP)
        )

    def get_total_time(self) -> timer.Time:
        seen_problems = self.problem_list.filter_by_status(
            plist.ProblemStatus.CORRECT, plist.ProblemStatus.WRONG,
            plist.ProblemStatus.SKIP
        )
        return seen_problems.get_total_time()

    def get_fastest_problem(self) -> Optional[plist.Problem]:
        return self.problem_list.get_fastest_problem()

    def get_slowest_problem(self) -> Optional[plist.Problem]:
        return self.problem_list.get_slowest_problem()
