from __future__ import annotations

import csv
import os

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.problem_list as plist

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Dict, List, Optional, Union
    import tsumemi.src.tsumemi.timer as timer
    PathLike = Union[str, os.PathLike]


class ProblemListController:
    """Controller object for a problem list. Handles access to its
    underlying problem list (model).
    """
    def __init__(self) -> None:
        self.problem_list: plist.ProblemList = plist.ProblemList()
        self.directory: Optional[PathLike] = None
        return

    def get_current_problem(self) -> Optional[plist.Problem]:
        return self.problem_list.curr_prob

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

    def make_problem_list_pane(self, parent: tk.Widget, *args, **kwargs
        ) -> ProblemListPane:
        return ProblemListPane(parent, self.problem_list, *args, **kwargs)

    def set_directory(self, directory: PathLike, recursive: bool = False
        ) -> Optional[plist.Problem]:
        """Open directory and set own problem list to contents.
        """
        self.problem_list.clear(suppress=True)
        self._add_problems_in_directory(
            directory, recursive=recursive, suppress=True
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

    def _add_problems_in_directory(self, directory: PathLike,
            recursive: bool = False, suppress: bool = False
        ) -> None:
        # Adds all problems in given directory.
        new_problems: List[plist.Problem] = []
        if recursive:
            for dirpath, _, filenames in os.walk(directory):
                new_problems.extend([
                    plist.Problem(os.path.join(dirpath, filename))
                    for filename in filenames
                    if filename.endswith(".kif")
                    or filename.endswith(".kifu")
                ])
        else:
            with os.scandir(directory) as it:
                new_problems = [
                    plist.Problem(os.path.join(directory, entry.name))
                    for entry in it
                    if entry.name.endswith(".kif")
                    or entry.name.endswith(".kifu")
                ]
        self.problem_list.add_problems(new_problems, suppress=suppress)
        return


class ProblemsView(ttk.Treeview, evt.IObserver):
    """GUI class to display list of problems.
    Observes underlying problem list and updates its view as needed.
    """
    def __init__(self, parent: tk.Widget, problem_list: plist.ProblemList,
            *args, **kwargs
        ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.problem_list: plist.ProblemList = problem_list
        self.problem_list.add_observer(self)
        self.set_callbacks({
            plist.ProbStatusEvent: self.display_status,
            plist.ProbTimeEvent: self.display_time,
            plist.ProbListEvent: self.refresh_view,
        })

        self.status_strings: Dict[plist.ProblemStatus, str] = {
            plist.ProblemStatus.NONE: "",
            plist.ProblemStatus.SKIP: "-",
            plist.ProblemStatus.CORRECT: "O",
            plist.ProblemStatus.WRONG: "X",
        }

        self["columns"] = ("filename", "time", "status")
        self["show"] = "headings"
        self.heading(
            "filename", text="Problem", command=self.problem_list.sort_by_file
        )
        self.heading(
            "time", text="Time", command=self.problem_list.sort_by_time
        )
        self.column("time", width=120)
        self.heading(
            "status", text="Status", command=self.problem_list.sort_by_status
        )
        self.column("status", anchor="center", width=40)
        # Colours to be decided (accessibility concerns)
        self.tag_configure("SKIP", background="snow2")
        self.tag_configure("CORRECT", background="PaleGreen1")
        self.tag_configure("WRONG", background="LightPink1")

        # Bind double click to go to problem
        def _click_to_prob(event: tk.Event) -> None:
            idx = self.get_idx_on_click(event)
            if idx is not None:
                self.problem_list.go_to_idx(idx)
            return
        self.bind("<Double-1>", _click_to_prob)
        return

    def display_time(self, event: plist.ProbTimeEvent) -> None:
        idx = event.idx
        time = event.time
        # Set time column for item at given index
        _id = self.get_children()[idx]
        self.set(_id, column="time", value=str(time))
        return

    def display_status(self, event: plist.ProbStatusEvent) -> None:
        idx = event.idx
        status = event.status
        _id = self.get_children()[idx]
        self.set(_id, column="status", value=self.status_strings[status])
        self.item(_id, tags=[status.name]) # overrides existing tags
        return

    def refresh_view(self, event: plist.ProbListEvent) -> None:
        # Refresh the entire view as the model changed, e.g. on opening folder
        problem_list = event.sender
        self.delete(*self.get_children())
        for problem in problem_list:
            filename = os.path.basename(problem.filepath)
            time_str = ("-" if problem.time is None
                else problem.time.to_hms_str(places=1)
            )
            status_str = self.status_strings[problem.status]
            self.insert(
                "", "end",
                values=(filename, time_str, status_str),
                tags=[problem.status.name]
            )
        return

    def get_idx_on_click(self, event: tk.Event) -> Optional[int]:
        if self.identify_region(event.x, event.y) == "cell":
            idx = self.index(self.identify_row(event.y))
            assert isinstance(idx, int) # tkinter missing stub?
            return idx
        else:
            return None


class ProblemListPane(ttk.Frame):
    """GUI frame containing view of problem list and associated
    controls.
    """
    def __init__(self,
            parent: tk.Widget, problem_list: plist.ProblemList,
            *args, **kwargs
        ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.problem_list: plist.ProblemList = problem_list

        # Display problem list as Treeview
        self.tvw: ProblemsView = ProblemsView(
            parent=self, problem_list=problem_list
        )

        # Make scrollbar
        self.scrollbar_tvw: ttk.Scrollbar = ttk.Scrollbar(
            self, orient="vertical",
            command=self.tvw.yview
        )
        self.tvw["yscrollcommand"] = self.scrollbar_tvw.set

        self.btn_randomise: ttk.Button = ttk.Button(
            self, text="Randomise problems",
            command=self.problem_list.randomise
        )

        self.tvw.grid(row=0, column=0, sticky="NSEW")
        self.scrollbar_tvw.grid(row=0, column=1, sticky="NS")
        self.btn_randomise.grid(row=1, column=0)
        return


class ProblemListStats:
    """A helper object that can be queried for the solving statistics
    of the problems inside the problem list it refers to.
    """
    def __init__(self,
            problem_list = plist.ProblemList,
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
