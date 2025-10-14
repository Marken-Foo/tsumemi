from __future__ import annotations

import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.problem as pb
import tsumemi.src.tsumemi.problem_list.problem_list_model as plist

from tsumemi.src.tsumemi import utils

if TYPE_CHECKING:
    from typing import Dict, Optional
    from tsumemi.src.tsumemi.problem_list.problem_list_viewmodel import (
        ProblemListViewModel,
    )


class ProblemsTreeviewFrame(utils.ScrollableTreeviewFrame, evt.IObserver):
    """GUI class to display list of problems.
    Observes underlying problem list and updates its view as needed.
    """

    def __init__(self, parent: tk.Widget, viewmodel: ProblemListViewModel) -> None:
        utils.ScrollableTreeviewFrame.__init__(self, parent, selectmode="none")
        evt.IObserver.__init__(self)
        self.viewmodel = viewmodel
        self.set_callbacks(
            {
                plist.ProbSelectedEvent: self.go_to_problem,
                plist.ProbStatusEvent: self.display_status,
                plist.ProbTimeEvent: self.display_time,
                plist.ProbListEvent: self.refresh_view,
            }
        )

        self.status_strings: Dict[pb.ProblemStatus, str] = {
            pb.ProblemStatus.NONE: "",
            pb.ProblemStatus.SKIP: "-",
            pb.ProblemStatus.CORRECT: "O",
            pb.ProblemStatus.WRONG: "X",
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
            iid = self._get_iid_on_click(event)
            if iid:
                self.set_focus(iid)
                self.viewmodel.go_to_problem(self.tvw.index(iid))
            return

        self.tvw.bind("<Double-1>", _click_to_prob)
        return

    def _unbind_double_click(self) -> None:
        self.tvw.unbind("<Double-1>")
        return

    def _bind_up_down(self, _event: Optional[tk.Event] = None) -> None:
        self.tvw.bind("<Key-Up>", self.viewmodel.go_prev_problem)
        self.tvw.bind("<Key-Down>", self.viewmodel.go_next_problem)
        return

    def _unbind_up_down(self, _event: Optional[tk.Event] = None) -> None:
        self.tvw.unbind("<Key-Up>")
        self.tvw.unbind("<Key-Down>")
        return

    def _bind_heading_commands(self) -> None:
        self.tvw.heading("filename", command=self.viewmodel.sort_by_file)
        self.tvw.heading("time", command=self.viewmodel.sort_by_time)
        self.tvw.heading("status", command=self.viewmodel.sort_by_status)
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

    def set_focus(self, iid: str) -> None:
        self.tvw.focus(iid)
        self.tvw.selection_set(iid)
        self.tvw.see(iid)
        return

    def disable_input(self) -> None:
        self._unbind_heading_commands()
        self._unbind_double_click()
        self._unbind_up_down()
        self._unbind_focus()
        return

    def enable_input(self) -> None:
        self._bind_heading_commands()
        self._bind_double_click()
        self._bind_focus()
        return

    def display_time(self, event: plist.ProbTimeEvent) -> None:
        idx = event.idx
        time = event.time
        # Set time column for item at given index
        id_ = self._idx_to_iid(idx)
        self.tvw.set(id_, column="time", value=str(time))
        return

    def display_status(self, event: plist.ProbStatusEvent) -> None:
        idx = event.idx
        status = event.status
        id_ = self._idx_to_iid(idx)
        self.tvw.set(id_, column="status", value=self.status_strings[status])
        self.tvw.item(id_, tags=[status.name])  # overrides existing tags
        return

    def go_to_problem(self, event: plist.ProbSelectedEvent) -> None:
        idx = event.sender.curr_prob_idx
        if idx is None:
            return
        id_ = self._idx_to_iid(idx)
        self.set_focus(id_)
        return

    def refresh_view(self, event: plist.ProbListEvent) -> None:
        # Refresh the entire view as the model changed, e.g. on opening folder
        problem_list = event.sender
        self.clear_treeview()
        for problem in problem_list:
            time_str = (
                "-" if problem.time is None else problem.time.to_hms_str(places=1)
            )
            status_str = self.status_strings[problem.status]
            tag_list = [problem.status.name]
            self.tvw.insert(
                "", "end", values=(problem.name, time_str, status_str), tags=tag_list
            )
        self.refresh_vsb()
        return

    def _idx_to_iid(self, idx: int) -> str:
        return self.tvw.get_children()[idx]

    def _get_iid_on_click(self, event: tk.Event) -> str:
        iid = self.tvw.identify("item", event.x, event.y)
        assert isinstance(iid, str)  # tkinter missing stub?
        return iid


class ProblemListPane(ttk.Frame):
    """GUI frame containing view of problem list and associated
    controls.
    """

    def __init__(self, parent: tk.Widget, viewmodel: ProblemListViewModel) -> None:
        ttk.Frame.__init__(self, parent)
        self.tvwfrm_problems = ProblemsTreeviewFrame(self, viewmodel)

        self.btn_randomise: ttk.Button = ttk.Button(
            self, text="Randomise problems", command=viewmodel.randomise
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.tvwfrm_problems.grid(row=0, column=0, sticky="NSEW")
        self.btn_randomise.grid(row=1, column=0)
        return
