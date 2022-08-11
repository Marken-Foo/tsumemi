from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Any, Callable


class GameNavButtonsFrame(ttk.Frame):
    """A GUI frame that provides basic move navigation controls.
    """
    def __init__(self, parent: tk.Widget) -> None:
        ttk.Frame.__init__(self, parent)
        # make |<<, <, >, >>| buttons
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=5)
        self.grid_rowconfigure(0, weight=1)
        self.grid_configure(padx=5, pady=5)
        # Define then grid buttons in self
        self.btn_far_left = ttk.Button(self, text="|<<")
        self.btn_left = ttk.Button(self, text="<")
        self.btn_right = ttk.Button(self, text=">")
        self.btn_far_right = ttk.Button(self, text=">>|")

        self.btn_far_left.grid_configure(padx=1, pady=1)
        self.btn_left.grid_configure(padx=1, pady=1)
        self.btn_right.grid_configure(padx=1, pady=1)
        self.btn_far_right.grid_configure(padx=1, pady=1)

        self.btn_far_left.grid(row=1, column=1, ipadx=0, sticky="NSEW")
        self.btn_left.grid(row=1, column=2, ipadx=0, sticky="NSEW")
        self.btn_right.grid(row=1, column=3, ipadx=0, sticky="NSEW")
        self.btn_far_right.grid(row=1, column=4, ipadx=0, sticky="NSEW")
        return

    def add_command_btn_far_left(self, cmd: Callable[..., Any]) -> None:
        self.btn_far_left.configure(command=cmd)
        return

    def add_command_btn_left(self, cmd: Callable[..., Any]) -> None:
        self.btn_left.configure(command=cmd)
        return

    def add_command_btn_right(self, cmd: Callable[..., Any]) -> None:
        self.btn_right.configure(command=cmd)
        return

    def add_command_btn_far_right(self, cmd: Callable[..., Any]) -> None:
        self.btn_far_right.configure(command=cmd)
        return
