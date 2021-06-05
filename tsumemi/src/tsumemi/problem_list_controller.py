from __future__ import annotations

import os

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.problem_list as plist
import tsumemi.src.tsumemi.timer as timer

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Any, Dict, Optional, Union
    tkWidget = Union[ttk.Widget, tk.Widget]


class ProblemListController:
    """Controller object for a problem list. Handles access to its
    underlying problem list (model) and GUI (view).
    """
    def __init__(self, parent: tkWidget, controller: Any, *args, **kwargs
        ) -> None:
        self.problem_list: plist.ProblemList = plist.ProblemList()
        self.view: ProblemListPane = ProblemListPane(
            parent, controller, self.problem_list,
            *args, **kwargs
        )
        return


class ProblemsView(ttk.Treeview, evt.IObserver):
    """GUI class to display list of problems.
    Observes underlying problem list and updates its view as needed.
    """
    def __init__(self, parent: tkWidget, controller: Any,
            problem_list: plist.ProblemList,
            *args, **kwargs
        ) -> None:
        self.controller: Any = controller
        super().__init__(parent, *args, **kwargs)
        self.problem_list: plist.ProblemList = problem_list
        self.problem_list.add_observer(self)
        self.NOTIFY_ACTIONS = {
            plist.ProbStatusEvent: self.display_status,
            plist.ProbTimeEvent: self.display_time,
            plist.ProbListEvent: self.refresh_view,
        }
        
        self.status_strings: Dict[plist.ProblemStatus, str] = {
            plist.ProblemStatus.NONE: "",
            plist.ProblemStatus.SKIP: "-",
            plist.ProblemStatus.CORRECT: "O",
            plist.ProblemStatus.WRONG: "X",
        }
        
        self["columns"] = ("filename", "time", "status")
        self["show"] = "headings"
        self.heading("filename", text="Problem", command=self.problem_list.sort_by_file)
        self.heading("time", text="Time", command=self.problem_list.sort_by_time)
        self.column("time", width=120)
        self.heading("status", text="Status", command=self.problem_list.sort_by_status)
        self.column("status", anchor="center", width=40)
        # Colours to be decided (accessibility concerns)
        self.tag_configure("SKIP", background="snow2")
        self.tag_configure("CORRECT", background="PaleGreen1")
        self.tag_configure("WRONG", background="LightPink1")
        
        # Bind double click to go to problem
        self.bind("<Double-1>",
            lambda e: self.controller.model.go_to_file(
                idx=self.get_idx_on_click(e)
            )
        )
        return
    
    def display_time(self, event: plist.ProbTimeEvent) -> None:
        idx = event.idx
        time = event.time
        # Set time column for item at given index
        id = self.get_children()[idx]
        time_str = timer.sec_to_str(time)
        self.set(id, column="time", value=time_str)
        return
    
    def display_status(self, event: plist.ProbStatusEvent) -> None:
        idx = event.idx
        status = event.status
        id = self.get_children()[idx]
        self.set(id, column="status", value=self.status_strings[status])
        self.item(id, tags=[status.name]) # overrides existing tags
        return
    
    def refresh_view(self, event: plist.ProbListEvent) -> None:
        # Refresh the entire view as the model changed, e.g. on opening folder
        problems = event.prob_list
        self.delete(*self.get_children())
        for problem in problems:
            filename = os.path.basename(problem.filepath)
            time_str = ("-" if problem.time is None
                else timer.sec_to_str(problem.time)
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
    def __init__(self, parent: tkWidget, controller: Any,
            problem_list: plist.ProblemList,
            *args, **kwargs
        ) -> None :
        self.controller: Any = controller
        super().__init__(parent, *args, **kwargs)
        self.problem_list: plist.ProblemList = problem_list
        
        # Display problem list as Treeview
        self.tvw: ProblemsView = ProblemsView(
            parent=self, controller=controller, problem_list=problem_list
        )
        self.tvw.grid(column=0, row=0, sticky="NSEW")
        
        # Make scrollbar
        self.scrollbar_tvw: ttk.Scrollbar = ttk.Scrollbar(
            self, orient="vertical",
            command=self.tvw.yview
        )
        self.scrollbar_tvw.grid(column=1, row=0, sticky="NS")
        self.tvw["yscrollcommand"] = self.scrollbar_tvw.set
        
        self.btn_randomise: ttk.Button = ttk.Button(
            self, text="Randomise problems",
            command=self.problem_list.randomise
        )
        self.btn_randomise.grid(column=0, row=1)
        
        self.btn_speedrun: ttk.Button = ttk.Button(
            self, text="Start speedrun",
            command=controller.model.start_speedrun
        )
        self.btn_speedrun.grid(column=0, row=2)
        self.btn_speedrun.grid_remove()
        
        self.btn_abort_speedrun: ttk.Button = ttk.Button(
            self, text="Abort speedrun",
            command=controller.model.abort_speedrun
        )
        self.btn_abort_speedrun.grid(column=0, row=2)
        self.btn_abort_speedrun.grid_remove()
        
        self.btn_speedrun.grid()
        return

