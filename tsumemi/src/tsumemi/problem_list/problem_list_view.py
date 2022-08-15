from __future__ import annotations

import os
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.problem_list.problem_list_model as plist

from tsumemi.src.tsumemi import utils

if TYPE_CHECKING:
    from typing import Dict, Optional
    from tsumemi.src.tsumemi.problem_list.problem_list_controller import ProblemListController


class ProblemsTreeviewFrame(utils.ScrollableTreeviewFrame, evt.IObserver):
    """GUI class to display list of problems.
    Observes underlying problem list and updates its view as needed.
    """
    def __init__(self, parent: tk.Widget, controller: ProblemListController
        ) -> None:
        utils.ScrollableTreeviewFrame.__init__(self, parent)
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

        self.tvw["columns"] = ("filename", "time", "status")
        self.tvw["show"] = "headings"
        self.tvw.heading("filename", text="Problem")
        self.tvw.heading("time", text="Time")
        self.tvw.column("time", width=120)
        self.tvw.heading("status", text="Status")
        self.tvw.column("status", anchor="center", width=40)
        # Colours to be decided (accessibility concerns)
        self.tvw.tag_configure("SKIP", background="snow2")
        self.tvw.tag_configure("CORRECT", background="PaleGreen1")
        self.tvw.tag_configure("WRONG", background="LightPink1")
        self._bind_double_click()
        self._bind_heading_commands()
        self._bind_focus()
        return

    def _bind_double_click(self) -> None:
        # Bind double click to go to problem
        def _click_to_prob(event: tk.Event) -> None:
            idx = self.get_idx_on_click(event)
            if idx is not None:
                self.controller.go_to_problem(idx)
            return
        self.tvw.bind("<Double-1>", _click_to_prob)
        return

    def _unbind_double_click(self) -> None:
        self.tvw.unbind("<Double-1>")
        return

    def _bind_up_down(self, event: Optional[tk.Event] = None) -> None:
        self.tvw.bind("<Key-Up>", self.controller.go_prev_problem)
        self.tvw.bind("<Key-Down>", self.controller.go_next_problem)
        return

    def _unbind_up_down(self, event: Optional[tk.Event] = None) -> None:
        self.tvw.unbind("<Key-Up>")
        self.tvw.unbind("<Key-Down>")
        return

    def _bind_heading_commands(self) -> None:
        self.tvw.heading("filename", command=self.controller.sort_by_file)
        self.tvw.heading("time", command=self.controller.sort_by_time)
        self.tvw.heading("status", command=self.controller.sort_by_status)
        return

    def _unbind_heading_commands(self) -> None:
        self.tvw.heading("filename", command="")
        self.tvw.heading("time", command="")
        self.tvw.heading("status", command="")
        return

    def _bind_focus(self) -> None:
        self.tvw.bind("<FocusIn>", self._bind_up_down)
        self.tvw.bind("<FocusOut>", self._unbind_up_down)
        return

    def _unbind_focus(self) -> None:
        self.tvw.unbind("<FocusIn>")
        self.tvw.unbind("<FocusOut>")
        return

    def disable_input(self) -> None:
        self._unbind_heading_commands()
        self._unbind_double_click()
        # self._unbind_up_down()
        self._unbind_focus()
        return

    def enable_input(self) -> None:
        self._bind_heading_commands()
        self._bind_double_click()
        self._bind_up_down()
        self._bind_focus()
        return

    def display_time(self, event: plist.ProbTimeEvent) -> None:
        idx = event.idx
        time = event.time
        # Set time column for item at given index
        _id = self.tvw.get_children()[idx]
        self.tvw.set(_id, column="time", value=str(time))
        return

    def display_status(self, event: plist.ProbStatusEvent) -> None:
        idx = event.idx
        status = event.status
        _id = self.tvw.get_children()[idx]
        self.tvw.set(_id, column="status", value=self.status_strings[status])
        self.tvw.item(_id, tags=[status.name]) # overrides existing tags
        return

    def refresh_view(self, event: plist.ProbListEvent) -> None:
        # Refresh the entire view as the model changed, e.g. on opening folder
        problem_list = event.sender
        self.clear_treeview()
        for problem in problem_list:
            filename = os.path.basename(problem.filepath)
            time_str = ("-" if problem.time is None
                else problem.time.to_hms_str(places=1)
            )
            status_str = self.status_strings[problem.status]
            self.tvw.insert(
                "", "end",
                values=(filename, time_str, status_str),
                tags=[problem.status.name]
            )
        self.refresh_vsb()
        return

    def get_idx_on_click(self, event: tk.Event) -> Optional[int]:
        if self.tvw.identify_region(event.x, event.y) == "cell":
            idx = self.tvw.index(self.tvw.identify_row(event.y))
            assert isinstance(idx, int) # tkinter missing stub?
            return idx
        return None


class ProblemListPane(ttk.Frame):
    """GUI frame containing view of problem list and associated
    controls.
    """
    def __init__(self, parent: tk.Widget, controller: ProblemListController
        ) -> None:
        ttk.Frame.__init__(self, parent)
        self.controller: ProblemListController = controller
        self.tvwfrm_problems = ProblemsTreeviewFrame(self, controller)

        self.btn_randomise: ttk.Button = ttk.Button(
            self, text="Randomise problems",
            command=self.controller.randomise
        )

        self.tvwfrm_problems.grid(row=0, column=0, sticky="NSEW")
        self.btn_randomise.grid(row=1, column=0)
        return
