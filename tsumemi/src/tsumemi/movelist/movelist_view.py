from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.movelist.movelist_viewmodel import MovelistViewModel

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Optional


class MovelistFrame(ttk.Frame):
    def __init__(self,
            parent: tk.Widget, *args, **kwargs
        ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.tvw: Optional[MovelistTreeview] = None
        self.scrollbar_tvw: Optional[ttk.Scrollbar] = None
        return

    def add_treeview(self, tvw: MovelistTreeview) -> None:
        self.tvw = tvw
        # Make scrollbar
        self.scrollbar_tvw = ttk.Scrollbar(
            self, orient="vertical", command=self.tvw.yview
        )
        self.tvw["yscrollcommand"] = self.scrollbar_tvw.set

        self.tvw.grid(row=0, column=0, sticky="NSEW")
        self.scrollbar_tvw.grid(row=0, column=1, sticky="NS")
        return

    def refresh_content(self) -> None:
        if self.tvw is not None:
            self.tvw.refresh_view()
        return


class MovelistTreeview(ttk.Treeview):
    def __init__(self, parent: tk.Widget, viewmodel: MovelistViewModel) -> None:
        ttk.Treeview.__init__(self, parent)
        self.viewmodel = viewmodel
        self["columns"] = ("move",)
        self["show"] = "headings"
        self.heading("move", text="Move")
        return

    def refresh_view(self) -> None:
        self.delete(*self.get_children())
        self.viewmodel.populate_treeview(self)
        return
