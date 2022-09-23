from __future__ import annotations

import tkinter as tk

from tkinter import font, ttk

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional


class NavControlFrame(ttk.Frame):
    """Frame containing navigation controls during a speedrun.
    """
    def __init__(self, parent: tk.Widget, flip_board: Callable[[bool], None]
        ) -> None:
        ttk.Frame.__init__(self, parent)
        self.nav_controls = ttk.Frame(self)
        want_upside_down = tk.BooleanVar(value=False)
        self.chk_upside_down = ttk.Checkbutton(
            self,
            text="Upside-down mode",
            command=lambda: flip_board(want_upside_down.get()),
            variable=want_upside_down, onvalue=True, offvalue=False
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.regrid()
        return

    def set_new_nav_controls(self,
            nav_pane_constructor: Callable[[tk.Widget], ttk.Frame]
        ) -> None:
        """Sets the nav control pane to a new instance, created by
        the constructor passed in. If no controller is passed in,
        defaults to a normal nav pane.
        """
        new_nav_controls = nav_pane_constructor(self)
        self.nav_controls.grid_forget()
        self.nav_controls = new_nav_controls
        self.regrid()
        return

    def regrid(self) -> None:
        self.nav_controls.grid(row=0, column=0)
        self.chk_upside_down.grid(row=1, column=0)
        return

    def make_nav_pane_normal(self,
            parent: tk.Widget,
            callable_prev: Callable[[], None],
            callable_toggle_solution: Callable[[], None],
            callable_next: Callable[[], None],
        ) -> ttk.Frame:
        nav = ttk.Frame(parent)
        btn_prev = ttk.Button(nav,
            text="< Prev",
            command=callable_prev,
        )
        btn_toggle_solution = ttk.Button(nav,
            text="Show/hide solution",
            command=callable_toggle_solution,
        )
        btn_next = ttk.Button(nav,
            text="Next >",
            command=callable_next,
        )
        btn_prev.grid(
            row=0, column=0, sticky="E",
            padx=5, pady=5,
        )
        btn_toggle_solution.grid(
            row=0, column=1, sticky="S",
            padx=5, pady=5,
        )
        btn_next.grid(
            row=0, column=2, sticky="W",
            padx=5, pady=5,
        )
        return nav


class SpeedrunFrame(ttk.Frame):
    """Frame containing speedrun controls.
    """
    def __init__(self,
            parent: tk.Widget,
            start_speedrun: Callable[[], None],
            abort_speedrun: Callable[[], None],
        ) -> None:
        ttk.Frame.__init__(self, parent)
        self.btn_speedrun: ttk.Button = ttk.Button(
            self,
            text="Start speedrun",
            command=start_speedrun
        )
        self.btn_abort_speedrun: ttk.Button = ttk.Button(
            self,
            text="Abort speedrun",
            command=abort_speedrun
        )
        self.btn_speedrun.grid(row=0, column=0)
        self.btn_abort_speedrun.grid(row=0, column=1)
        self.btn_abort_speedrun.config(state="disabled")
        return

    def allow_start_speedrun(self) -> None:
        self.btn_speedrun.config(state="normal")
        self.btn_abort_speedrun.config(state="disabled")
        return

    def allow_abort_speedrun(self) -> None:
        self.btn_speedrun.config(state="disabled")
        self.btn_abort_speedrun.config(state="normal")
        return


class SolutionLabel(tk.Label):
    """Label to display, show, and hide problem solutions.
    """
    def __init__(self, parent: tk.Widget, *args: Any, **kwargs: Any) -> None:
        tk.Label.__init__(self, parent, *args, **kwargs)
        self.is_solution_shown: bool = True
        self.solution_text: str = "\nOpen a folder of problems to display.\n"
        self.textvar: tk.StringVar = tk.StringVar(value=self.solution_text)
        self["textvariable"] = self.textvar

        defaultfont = font.Font(font=self["font"])
        typeface = defaultfont["family"]
        fontsize = defaultfont["size"]
        self.config(font=(typeface, fontsize+2))
        return

    def set_solution_text(self, text: str) -> None:
        self.solution_text = text
        return

    def hide_solution(self) -> None:
        self.textvar.set("[solution hidden]")
        self.is_solution_shown = False
        return

    def show_solution(self) -> None:
        self.textvar.set(self.solution_text)
        self.is_solution_shown = True
        return

    def toggle_solution(self, _event: Optional[tk.Event] = None) -> None:
        if self.is_solution_shown:
            self.hide_solution()
        else:
            self.show_solution()
        return
