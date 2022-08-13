from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.movelist.movelist_viewmodel import MovelistViewModel
from tsumemi.src.tsumemi.movelist.movelist_view import MovelistFrame

if TYPE_CHECKING:
    import tkinter as tk
    from tsumemi.src.shogi.notation_writer import AbstractMoveWriter
    from tsumemi.src.tsumemi.game.game_model import GameModel


class MovelistController:
    def __init__(self,
            game: GameModel,
            move_writer: AbstractMoveWriter
        ) -> None:
        self.viewmodel = MovelistViewModel(game, move_writer)
        return

    def make_movelist_view(self, parent_widget: tk.Widget) -> MovelistFrame:
        movelist_frame = MovelistFrame(parent_widget, self.viewmodel)
        tvw = movelist_frame.tvw
        var_tvw = movelist_frame.var_tvw
        self.viewmodel.game.add_observer(tvw)
        self.viewmodel.game.add_observer(var_tvw)
        tvw.refresh_view()
        return movelist_frame

    def update_move_writer(self, move_writer: AbstractMoveWriter) -> None:
        self.viewmodel.move_writer = move_writer
        return
