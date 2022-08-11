from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.game.game_nav_btns_view import GameNavButtonsFrame

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Optional
    from tsumemi.src.tsumemi.movelist.movelist_viewmodel import MovelistViewModel


class MovelistFrame(ttk.Frame):
    def __init__(self,
            parent: tk.Widget, *args, **kwargs
        ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.tvw: Optional[MovelistTreeview] = None
        self.scrollbar_tvw: Optional[ttk.Scrollbar] = None
        self.frm_nav: GameNavButtonsFrame = GameNavButtonsFrame(self)
        return

    def add_treeview(self, tvw: MovelistTreeview) -> None:
        self.tvw = tvw
        # Make scrollbar
        self.scrollbar_tvw = ttk.Scrollbar(
            self, orient="vertical", command=self.tvw.yview
        )
        self.tvw["yscrollcommand"] = self.scrollbar_tvw.set

        self.bind_buttons()

        self.tvw.grid(row=0, column=0, sticky="NSEW")
        self.scrollbar_tvw.grid(row=0, column=1, sticky="NS")
        self.frm_nav.grid(row=1, column=0, columnspan=2, sticky="EW")
        return

    def bind_buttons(self) -> None:
        if self.tvw is not None:
            self.frm_nav.add_command_btn_far_left(
                self.tvw.viewmodel.go_to_start)
            self.frm_nav.add_command_btn_left(self.tvw.viewmodel.go_prev)
            self.frm_nav.add_command_btn_right(self.tvw.viewmodel.go_next)
            self.frm_nav.add_command_btn_far_right(self.tvw.viewmodel.go_to_end)
        return

    def refresh_content(self) -> None:
        if self.tvw is not None:
            self.tvw.refresh_view()
            self.bind_buttons()
        return


class MovelistTreeview(ttk.Treeview):
    def __init__(self, parent: tk.Widget, viewmodel: MovelistViewModel) -> None:
        ttk.Treeview.__init__(self, parent)
        self.viewmodel = viewmodel
        self["columns"] = ("movenum", "move", "alternative")
        self["show"] = "headings"
        self.heading("movenum", text="")
        self.column("movenum", width=10)
        self.heading("move", text="Move")
        self.column("move", width=50)
        self.heading("alternative", text="")
        self.column("alternative", width=10)
        return

    def refresh_view(self) -> None:
        self.delete(*self.get_children())
        self.viewmodel.populate_treeview(self)
        return
