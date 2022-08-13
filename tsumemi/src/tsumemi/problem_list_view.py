from __future__ import annotations

import os
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.problem_list as plist

if TYPE_CHECKING:
    from typing import Dict, Optional
    from tsumemi.src.tsumemi.problem_list_controller import ProblemListController


class ProblemsView(ttk.Treeview, evt.IObserver):
    """GUI class to display list of problems.
    Observes underlying problem list and updates its view as needed.
    """
    def __init__(self, parent: tk.Widget, controller: ProblemListController
        ) -> None:
        ttk.Treeview.__init__(self, parent)
        evt.IObserver.__init__(self)
        self.controller = controller
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
        self.heading("filename", text="Problem")
        self.heading("time", text="Time")
        self.column("time", width=120)
        self.heading("status", text="Status")
        self.column("status", anchor="center", width=40)
        # Colours to be decided (accessibility concerns)
        self.tag_configure("SKIP", background="snow2")
        self.tag_configure("CORRECT", background="PaleGreen1")
        self.tag_configure("WRONG", background="LightPink1")
        self._bind_double_click()
        self._bind_heading_commands()
        return

    def _bind_double_click(self) -> None:
        # Bind double click to go to problem
        def _click_to_prob(event: tk.Event) -> None:
            idx = self.get_idx_on_click(event)
            if idx is not None:
                self.controller.go_to_problem(idx)
            return
        self.bind("<Double-1>", _click_to_prob)
        return

    def _unbind_double_click(self) -> None:
        self.unbind("<Double-1>")
        return

    def _bind_heading_commands(self) -> None:
        self.heading("filename", command=self.controller.sort_by_file)
        self.heading("time", command=self.controller.sort_by_time)
        self.heading("status", command=self.controller.sort_by_status)
        return

    def disable_input(self) -> None:
        self._unbind_double_click()
        self.heading("filename", command="")
        self.heading("time", command="")
        self.heading("status", command="")
        return

    def enable_input(self) -> None:
        self._bind_double_click()
        self._bind_heading_commands()
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
    def __init__(self, parent: tk.Widget, controller: ProblemListController
        ) -> None:
        ttk.Frame.__init__(self, parent)
        self.controller: ProblemListController = controller
        self.tvw: ProblemsView = ProblemsView(self, controller)

        # Make scrollbar
        self.scrollbar_tvw: ttk.Scrollbar = ttk.Scrollbar(
            self, orient="vertical",
            command=self.tvw.yview
        )
        self.tvw["yscrollcommand"] = self.scrollbar_tvw.set

        self.btn_randomise: ttk.Button = ttk.Button(
            self, text="Randomise problems",
            command=self.controller.randomise
        )

        self.tvw.grid(row=0, column=0, sticky="NSEW")
        self.scrollbar_tvw.grid(row=0, column=1, sticky="NS")
        self.btn_randomise.grid(row=1, column=0)
        return
