from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Optional
    from tsumemi.src.tsumemi.problem_list.problem_list_model import Problem, ProblemList


class ProblemListViewModel:
    """Viewmodel for a problem list. Called by a view to feed
    information back to the underlying problem list.
    """
    def __init__(self, problem_list: ProblemList) -> None:
        self.problem_list = problem_list
        return

    def go_next_problem(self, event: Optional[tk.Event] = None
        ) -> Optional[Problem]:
        return self.problem_list.go_to_next()

    def go_prev_problem(self, event: Optional[tk.Event] = None
        ) -> Optional[Problem]:
        return self.problem_list.go_to_prev()

    def go_to_problem(self, idx: int = 0) -> Optional[Problem]:
        return self.problem_list.go_to_idx(idx)

    def sort_by_file(self) -> None:
        self.problem_list.sort_by_file()
        return

    def sort_by_time(self) -> None:
        self.problem_list.sort_by_time()
        return

    def sort_by_status(self) -> None:
        self.problem_list.sort_by_status()
        return

    def randomise(self) -> None:
        self.problem_list.randomise()
        return
