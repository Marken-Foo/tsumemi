from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk
    from tsumemi.src.tsumemi.game_controller import GameController


class NavigableGameFrame(ttk.Frame):
    """A GUI frame that displays a game and has basic move navigation
    controls underneath the board.
    """
    def __init__(self, parent: tk.Widget, controller: GameController,
            *args, **kwargs
        ) -> None:
        self.controller: GameController = controller
        super().__init__(parent, *args, **kwargs)
        # make board canvas
        self.board_canvas = controller.make_board_canvas(self)
        self.board_canvas.grid(row=0, column=0, sticky="NSEW")
        self.board_canvas.bind("<Configure>", self.board_canvas.on_resize)
        # make |<<, <, >, >>| buttons
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(row=1, column=0, sticky="NSEW")
        buttons_frame.grid_columnconfigure(0, weight=5)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)
        buttons_frame.grid_columnconfigure(3, weight=1)
        buttons_frame.grid_columnconfigure(4, weight=1)
        buttons_frame.grid_columnconfigure(5, weight=5)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_rowconfigure(1, weight=1)
        buttons_frame.grid_rowconfigure(2, weight=1)
        buttons_frame.grid_configure(padx=5, pady=5)
        # Define then grid buttons in buttons_frame
        btn_go_to_start = ttk.Button(
            buttons_frame, text="|<<", command=controller.go_to_start
        )
        btn_go_back = ttk.Button(
            buttons_frame, text="<", command=controller.go_prev_move
        )
        btn_go_forward = ttk.Button(
            buttons_frame, text=">", command=controller.go_next_move
        )
        btn_go_to_end = ttk.Button(
            buttons_frame, text=">>|", command=controller.go_to_end
        )
        self._buttons = [
            btn_go_to_start, btn_go_back, btn_go_forward, btn_go_to_end,
        ]
        for btn in self._buttons:
            btn.grid_configure(padx=1, pady=1)
        btn_go_to_start.grid(row=1, column=1, sticky="NSEW")
        btn_go_back.grid(row=1, column=2, sticky="NSEW")
        btn_go_forward.grid(row=1, column=3, sticky="NSEW")
        btn_go_to_end.grid(row=1, column=4, sticky="NSEW")
        return
