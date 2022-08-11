from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.game.game_nav_btns_view import GameNavButtonsFrame

if TYPE_CHECKING:
    import tkinter as tk
    import tsumemi.src.tsumemi.img_handlers as imghand
    from tsumemi.src.tsumemi.game.game_controller import GameController


class NavigableGameFrame(ttk.Frame):
    """A GUI frame that displays a game and has basic move navigation
    controls underneath the board.
    """
    def __init__(self,
            parent: tk.Widget,
            skin_settings: imghand.SkinSettings,
            controller: GameController
        ) -> None:
        self.controller: GameController = controller
        super().__init__(parent)
        # make board canvas
        self.board_canvas = controller.make_board_canvas(self, skin_settings)
        self.board_canvas.grid(row=0, column=0, sticky="NSEW")
        self.board_canvas.bind("<Configure>", self.board_canvas.on_resize)
        buttons_frame = GameNavButtonsFrame(self)
        buttons_frame.grid(row=1, column=0, sticky="NSEW")
        buttons_frame.add_command_btn_far_left(controller.go_to_start)
        buttons_frame.add_command_btn_left(controller.go_prev_move)
        buttons_frame.add_command_btn_right(controller.go_next_move)
        buttons_frame.add_command_btn_far_right(controller.go_to_end)
        self.buttons_frame = buttons_frame
        return
