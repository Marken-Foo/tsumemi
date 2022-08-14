from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt

from tsumemi.src.tsumemi import utils
from tsumemi.src.tsumemi.game.game_model import GameUpdateEvent
from tsumemi.src.tsumemi.game.game_nav_btns_view import GameNavButtonsFrame

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Optional
    from tsumemi.src.tsumemi.movelist.movelist_viewmodel import MovelistViewModel


class MovelistFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, viewmodel: MovelistViewModel) -> None:
        ttk.Frame.__init__(self, parent)
        self.tvwfrm_movelist = MovelistTreeviewFrame(self, viewmodel)
        self.tvwfrm_variations = VariationTreeviewFrame(self, viewmodel)
        self.frm_nav = GameNavButtonsFrame(self)
        self.bind_buttons()

        self.tvwfrm_movelist.grid(row=0, column=0, sticky="NSEW")
        self.frm_nav.grid(row=1, column=0, sticky="")
        self.tvwfrm_variations.grid(row=2, column=0)
        return

    def bind_buttons(self) -> None:
        if self.tvwfrm_movelist is None:
            return
        viewmodel = self.tvwfrm_movelist.viewmodel
        self.frm_nav.add_command_btn_far_left(viewmodel.go_to_start)
        self.frm_nav.add_command_btn_left(viewmodel.go_prev)
        self.frm_nav.add_command_btn_right(viewmodel.go_next)
        self.frm_nav.add_command_btn_far_right(viewmodel.go_to_end)
        return

    def refresh_content(self) -> None:
        if self.tvwfrm_movelist is not None:
            self.tvwfrm_movelist.refresh_view()
            self.bind_buttons()
        return

    def disable_display(self) -> None:
        self.tvwfrm_movelist.disable()
        self.tvwfrm_variations.disable()
        self.frm_nav.disable()
        return

    def enable_display(self) -> None:
        self.tvwfrm_movelist.enable()
        self.tvwfrm_variations.enable()
        self.frm_nav.enable()
        return


class MovelistTreeviewFrame(utils.ScrollableTreeviewFrame, evt.IObserver):
    def __init__(self, parent: tk.Widget, viewmodel: MovelistViewModel) -> None:
        utils.ScrollableTreeviewFrame.__init__(self, parent, show="headings")
        evt.IObserver.__init__(self)
        self.viewmodel = viewmodel

        self.tvw["columns"] = ("movenum", "move", "alternative")
        self.tvw.heading("movenum", text="")
        self.tvw.column("movenum", width=10)
        self.tvw.heading("move", text="Move")
        self.tvw.column("move")
        self.tvw.heading("alternative", text="")
        self.tvw.column("alternative", width=10)

        self.set_callbacks({GameUpdateEvent: self.refresh_view})
        self._bind_click()
        return

    def _bind_click(self) -> None:
        # Bind single click to go to a move
        def _click_to_position(event: tk.Event) -> None:
            iid_str = self.tvw.identify("item", event.x, event.y)
            if iid_str:
                self.viewmodel.go_to_id(int(iid_str))
            return
        self.tvw.bind("<Button-1>", _click_to_position)
        return

    def _unbind_click(self) -> None:
        self.tvw.unbind("<Button-1>")
        return

    def set_focus(self, iid: str) -> None:
        self.tvw.focus(iid)
        self.tvw.selection_set(iid)
        self.tvw.see(iid)
        return

    def refresh_view(self, event: Optional[evt.Event] = None) -> None:
        # pylint: disable=unused-argument
        # (event is necessary as a callback)
        self.clear_treeview()
        self.viewmodel.populate_treeview(self.tvw)
        iid = str(self.viewmodel.game.game.curr_node.id)
        if self.tvw.exists(iid):
            self.set_focus(iid)
        self.refresh_vsb()
        return

    def enable(self) -> None:
        self.set_callbacks({GameUpdateEvent: self.refresh_view})
        self._bind_click()
        self.refresh_view()
        return

    def disable(self) -> None:
        self.set_callbacks({})
        self._unbind_click()
        self.clear_treeview()
        self.tvw.insert("", "end", values=("", "Hidden", ""))
        return


class VariationTreeviewFrame(utils.ScrollableTreeviewFrame, evt.IObserver):
    def __init__(self, parent: tk.Widget, viewmodel: MovelistViewModel) -> None:
        utils.ScrollableTreeviewFrame.__init__(
            self, parent, show="headings", height=3
        )
        evt.IObserver.__init__(self)
        self.viewmodel = viewmodel
        self.tvw["columns"] = ("priority", "move")
        self.tvw.heading("priority", text="")
        self.tvw.column("priority", width=10)
        self.tvw.heading("move", text="Variation")
        self.set_callbacks({GameUpdateEvent: self.refresh_view})
        self._bind_click()
        return

    def _bind_click(self) -> None:
        # Bind single click to go to a move
        def _click_to_position(event: tk.Event) -> None:
            iid_str = self.tvw.identify("item", event.x, event.y)
            if iid_str:
                self.viewmodel.go_to_id(int(iid_str))
            return
        self.tvw.bind("<Button-1>", _click_to_position)
        return

    def _unbind_click(self) -> None:
        self.tvw.unbind("<Button-1>")
        return

    def refresh_view(self, event: Optional[evt.Event] = None) -> None:
        # pylint: disable=unused-argument
        # (event is necessary as a callback)
        self.clear_treeview()
        self.viewmodel.populate_variation_treeview(self.tvw)
        return

    def enable(self) -> None:
        self.set_callbacks({GameUpdateEvent: self.refresh_view})
        self._bind_click()
        self.refresh_view()
        return

    def disable(self) -> None:
        self.set_callbacks({})
        self._unbind_click()
        self.clear_treeview()
        self.tvw.insert("", "end", values=("", "Hidden"))
        return
