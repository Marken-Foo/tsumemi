from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.movelist.movelist_viewmodel import MovelistViewModel
from tsumemi.src.tsumemi.movelist.movelist_view import MovelistFrame

if TYPE_CHECKING:
    import tkinter as tk
    from tsumemi.src.tsumemi.game.game_model import GameModel
    from tsumemi.src.tsumemi.notation_writer import NotationWriter


class MovelistController:
    def __init__(self,
            game: GameModel,
            notation_writer: NotationWriter
        ) -> None:
        self.viewmodel = MovelistViewModel(game, notation_writer)
        return

    def make_movelist_view(self, parent_widget: tk.Widget) -> MovelistFrame:
        movelist_frame = MovelistFrame(parent_widget, self.viewmodel)
        tvw = movelist_frame.tvwfrm_movelist
        var_tvw = movelist_frame.tvwfrm_variations
        self.viewmodel.game.add_observer(tvw)
        self.viewmodel.game.add_observer(var_tvw)
        tvw.refresh_view()
        return movelist_frame
