from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.board_canvas as bc
import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.move_input_handler as mih

from tsumemi.src.shogi.basetypes import TerminationMove
from tsumemi.src.shogi.game import Game

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Any, List, Tuple
    import tsumemi.src.tsumemi.img_handlers as imghand


class GameEndEvent(evt.Event):
    def __init__(self) -> None:
        return


class WrongMoveEvent(evt.Event):
    def __init__(self) -> None:
        return


class GameController(evt.Emitter, evt.IObserver):
    def __init__(self, skin_settings: imghand.SkinSettings) -> None:
        evt.Emitter.__init__(self)
        self.NOTIFY_ACTIONS = {}
        self.game = Game()
        self.views: List[bc.BoardCanvas] = []
        self.skin_settings = skin_settings
        self.set_free_mode()
        return
    
    def make_board_canvas(self, parent: tk.Widget,
            *args, **kwargs
        ) -> bc.BoardCanvas:
        """Creates a BoardCanvas to display the game.
        """
        board_canvas = bc.BoardCanvas(parent, self.game, self.skin_settings,
            bg="white", *args, **kwargs
        )
        move_input_handler = mih.MoveInputHandler(board_canvas)
        move_input_handler.add_observer(self)
        self.views.append(board_canvas)
        return board_canvas
    
    def make_navigable_view(self, parent: tk.Widget, *args, **kwargs
        ) -> Tuple[ttk.Frame, bc.BoardCanvas]:
        nav_game_frame = NavigableGameFrame(parent, self, *args, **kwargs)
        board_canvas = nav_game_frame.board_canvas
        move_input_handler = mih.MoveInputHandler(board_canvas)
        move_input_handler.add_observer(self)
        self.views.append(board_canvas)
        return nav_game_frame, board_canvas
    
    def get_current_sfen(self) -> str:
        return self.game.get_current_sfen()
    
    def set_game(self, game: Game) -> None:
        self.game = game
        for board_canvas in self.views:
            board_canvas.set_position(game.position)
        return
    
    def set_speedrun_mode(self) -> None:
        self.NOTIFY_ACTIONS[mih.MoveEvent] = self.verify_move
        return
    
    def set_free_mode(self) -> None:
        self.NOTIFY_ACTIONS[mih.MoveEvent] = self._add_move
        return
    
    def refresh_views(self) -> None:
        for board_canvas in self.views:
            board_canvas.draw()
        return
    
    def _add_move(self, event: mih.MoveEvent) -> None:
        """Make the move, regardless of whether the move is in the
        game or not.
        """
        move = event.move
        self.game.add_move(move)
        self.refresh_views()
        return
    
    def verify_move(self, event: mih.MoveEvent) -> None:
        # Used only in speedrun mode
        move = event.move
        if self.game.is_mainline(move):
            # the move is the mainline, so it is correct
            self.game.make_move(move)
            self.refresh_views()
            if self.game.is_end():
                self._notify_observers(GameEndEvent())
                return
            else:
                response_move = self.game.get_mainline_move()
                if type(response_move) == TerminationMove:
                    self._notify_observers(GameEndEvent())
                    return
                else:
                    self.game.make_move(response_move)
                    self.refresh_views()
                    if self.game.is_end():
                        self._notify_observers(GameEndEvent())
                    return
        else:
            self._notify_observers(WrongMoveEvent())
            return
    
    def go_to_start(self):
        self.game.go_to_start()
        self.refresh_views()
        return
    
    def go_to_end(self):
        self.game.go_to_end()
        self.refresh_views()
        return
    
    def go_next_move(self):
        self.game.go_next_move()
        self.refresh_views()
        return
    
    def go_prev_move(self):
        self.game.go_prev_move()
        self.refresh_views()
        return


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
        self.board_canvas.grid(column=0, row=0, sticky="NSEW")
        self.board_canvas.bind("<Configure>", self.board_canvas.on_resize)
        # make |<<, <, >, >>| buttons
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(column=0, row=1, sticky="NSEW")
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
        btn_go_to_start = ttk.Button(buttons_frame, text="|<<", command=controller.go_to_start)
        btn_go_to_start.grid(column=1, row=1, sticky="NSEW")
        btn_go_back = ttk.Button(buttons_frame, text="<", command=controller.go_prev_move)
        btn_go_back.grid(column=2, row=1, sticky="NSEW")
        btn_go_forward = ttk.Button(buttons_frame, text=">", command=controller.go_next_move)
        btn_go_forward.grid(column=3, row=1, sticky="NSEW")
        btn_go_to_end = ttk.Button(buttons_frame, text=">>|", command=controller.go_to_end)
        btn_go_to_end.grid(column=4, row=1, sticky="NSEW")
        self.buttons = [
            btn_go_to_start, btn_go_back, btn_go_forward, btn_go_to_end,
        ]
        for btn in self.buttons:
            btn.grid_configure(padx=1, pady=1)
        return
