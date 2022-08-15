from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Any


class ScrollableTreeviewFrame(ttk.Frame):
    """Utility GUI component for a vertically scrollable treeview.
    Implemented as a `ttk.Frame` with a `ttk.Treeview` and
    `ttk.Scrollbar` inside.
    """
    def __init__(self,
            parent: tk.Widget,
            *tvw_args: Any,
            **tvw_kwargs: Any
        ) -> None:
        """Initialises self as a `ttk.Frame`. Extra arguments are
        passed into `ttk.Frame.__init__` constructor.
        """
        ttk.Frame.__init__(self, parent)
        self.tvw = ttk.Treeview(self, *tvw_args, **tvw_kwargs)
        self.vsb = ttk.Scrollbar(
            self, orient="vertical", command=self.tvw.yview
        )
        self.tvw["yscrollcommand"] = self.vsb.set
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tvw.grid(row=0, column=0, sticky="NSEW")
        self.vsb.grid(row=0, column=1, sticky="NS")
        return

    def refresh_vsb(self) -> None:
        """Refreshes the scrollbar. Call in places where the length
        of the treeview may change.
        """
        self.tvw["yscrollcommand"] = self.vsb.set
        return

    def clear_treeview(self) -> None:
        """Removes all nodes from internal treeview.
        """
        self.tvw.delete(*self.tvw.get_children())
        return
