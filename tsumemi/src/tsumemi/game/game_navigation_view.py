from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.game.game_nav_btns_view import GameNavButtonsFrame

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Optional
    from tsumemi.src.tsumemi.board_gui.board_canvas import BoardCanvas


class NavigableGameFrame(ttk.Frame):
    """A GUI frame that displays a game and has basic move navigation
    controls underneath the board.
    """
    def __init__(self, parent: tk.Widget) -> None:
        ttk.Frame.__init__(self, parent)
        self.board_canvas: Optional[BoardCanvas] = None
        self.buttons_frame: Optional[GameNavButtonsFrame] = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        return

    def add_items(self,
            board_canvas: BoardCanvas, buttons_frame: GameNavButtonsFrame
        ) -> None:
        self.board_canvas = board_canvas
        self.board_canvas.grid(row=0, column=0, sticky="NSEW")
        self.board_canvas.bind("<Configure>", self.board_canvas.on_resize)
        self.buttons_frame = buttons_frame
        buttons_frame.grid(row=1, column=0, sticky="NSEW")
        return

    def disable_buttons(self) -> None:
        if self.buttons_frame is not None:
            self.buttons_frame.disable()
        return

    def enable_buttons(self) -> None:
        if self.buttons_frame is not None:
            self.buttons_frame.enable()
        return
