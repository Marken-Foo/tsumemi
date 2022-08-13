from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt

from tsumemi.src.tsumemi.game.game_model import GameUpdateEvent
from tsumemi.src.tsumemi.game.game_nav_btns_view import GameNavButtonsFrame

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Optional
    from tsumemi.src.shogi.gametree import MoveNodeId
    from tsumemi.src.tsumemi.movelist.movelist_viewmodel import MovelistViewModel


class MovelistFrame(ttk.Frame):
    def __init__(self,
            parent: tk.Widget, *args, **kwargs
        ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.tvw: Optional[MovelistTreeview] = None
        self.scrollbar_tvw: Optional[ttk.Scrollbar] = None
        self.frm_nav: GameNavButtonsFrame = GameNavButtonsFrame(self)
        self.var_tvw: Optional[MovelistVariationTvw] = None
        self.scrollbar_var_tvw: Optional[ttk.Scrollbar] = None
        return

    def add_treeview(self,
            tvw: MovelistTreeview,
            var_tvw: MovelistVariationTvw
        ) -> None:
        self.tvw = tvw
        self.var_tvw = var_tvw
        # Make scrollbar
        self.scrollbar_tvw = ttk.Scrollbar(
            self, orient="vertical", command=self.tvw.yview
        )
        self.tvw["yscrollcommand"] = self.scrollbar_tvw.set

        self.scrollbar_var_tvw = ttk.Scrollbar(
            self, orient="vertical", command=self.var_tvw.yview
        )
        self.var_tvw["yscrollcommand"] = self.scrollbar_var_tvw.set

        self.bind_buttons()

        self.tvw.grid(row=0, column=0, sticky="NSEW")
        self.scrollbar_tvw.grid(row=0, column=1, sticky="NS")
        self.frm_nav.grid(row=1, column=0, columnspan=2, sticky="")
        self.var_tvw.grid(row=2, column=0)
        self.scrollbar_var_tvw.grid(row=2, column=1, sticky="NS")
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


class MovelistTreeview(ttk.Treeview, evt.IObserver):
    def __init__(self, parent: tk.Widget, viewmodel: MovelistViewModel) -> None:
        ttk.Treeview.__init__(self, parent, show="headings")
        evt.IObserver.__init__(self)
        self.viewmodel = viewmodel
        self["columns"] = ("movenum", "move", "alternative")
        self.heading("movenum", text="")
        self.column("movenum", width=10)
        self.heading("move", text="Move")
        self.column("move")
        self.heading("alternative", text="")
        self.column("alternative", width=10)

        self.set_callbacks({GameUpdateEvent: self.refresh_view})

        # Bind single click to go to a move
        def _click_to_position(event: tk.Event) -> None:
            iid = int(self.identify("item", event.x, event.y))
            self.viewmodel.go_to_id(iid)
            return
        self.bind("<Button-1>", _click_to_position)
        return

    def set_focus(self, iid: MoveNodeId) -> None:
        self.focus(iid)
        self.selection_set(iid)
        self.see(iid)
        return

    def refresh_view(self, event: Optional[evt.Event] = None) -> None:
        self.delete(*self.get_children())
        self.viewmodel.populate_treeview(self)
        iid = str(self.viewmodel.game.game.curr_node.id)
        if self.exists(iid):
            self.set_focus(iid)
        return


class MovelistVariationTvw(ttk.Treeview, evt.IObserver):
    def __init__(self, parent: tk.Widget, viewmodel: MovelistViewModel) -> None:
        ttk.Treeview.__init__(self, parent, show="headings")
        evt.IObserver.__init__(self)
        self.viewmodel = viewmodel
        self["columns"] = ("priority", "move")
        self.heading("priority", text="")
        self.column("priority", width=10)
        self.heading("move", text="Variation")

        self.set_callbacks({GameUpdateEvent: self.refresh_view})
        return

    def refresh_view(self, event: Optional[evt.Event] = None) -> None:
        self.delete(*self.get_children())
        self.viewmodel.populate_variation_treeview(self)
        return
