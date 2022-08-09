from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.movelist.movelist_viewmodel import MovelistViewModel
from tsumemi.src.tsumemi.movelist.movelist_view import MovelistFrame, MovelistTreeview

if TYPE_CHECKING:
    import tkinter as tk
    from tsumemi.src.shogi.game import Game
    from tsumemi.src.shogi.notation_writer import AbstractMoveWriter


class MovelistController:
    def __init__(self,
            game: Game,
            move_writer: AbstractMoveWriter
        ) -> None:
        self.viewmodel = MovelistViewModel(game, move_writer)
        return

    def make_movelist_view(self, parent_widget: tk.Widget) -> MovelistFrame:
        movelist_frame = MovelistFrame(parent_widget)
        tvw = MovelistTreeview(movelist_frame, self.viewmodel)
        movelist_frame.add_treeview(tvw)
        tvw.refresh_view()
        return movelist_frame

    def update_move_writer(self, move_writer: AbstractMoveWriter) -> None:
        self.viewmodel.move_writer = move_writer
        return
