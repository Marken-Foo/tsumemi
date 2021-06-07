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
    from typing import Any, List
    import tsumemi.src.tsumemi.img_handlers as imghand


class GameEndEvent(evt.Event):
    def __init__(self) -> None:
        return


class WrongMoveEvent(evt.Event):
    def __init__(self) -> None:
        return


class GameController(evt.Emitter, evt.IObserver):
    def __init__(self) -> None:
        evt.Emitter.__init__(self)
        self.NOTIFY_ACTIONS = {}
        self.game = Game()
        self.views: List[bc.BoardCanvas] = []
        
        self.set_free_mode()
        return
    
    def make_board_canvas(self, parent: tk.Widget,
            skin_settings: imghand.SkinSettings,
            *args, **kwargs
        ) -> bc.BoardCanvas:
        board_canvas = bc.BoardCanvas(parent, self.game, skin_settings,
            bg="white", *args, **kwargs
        )
        move_input_handler = mih.MoveInputHandler(board_canvas)
        move_input_handler.add_observer(self)
        self.views.append(board_canvas)
        return board_canvas
    
    def set_game(self, game: Game) -> None:
        self.game = game
        for board_canvas in self.views:
            board_canvas.set_position(game.position)
        return
    
    def set_speedrun_mode(self) -> None:
        self.NOTIFY_ACTIONS[mih.MoveEvent] = self.verify_move
        return
    
    def set_free_mode(self) -> None:
        self.NOTIFY_ACTIONS[mih.MoveEvent] = self.add_move
        return
    
    def add_move(self, event: mih.MoveEvent) -> None:
        """Make the move, regardless of whether the move is in the
        game or not.
        """
        move = event.move
        self.game.add_move(move)
        for board_canvas in self.views:
            board_canvas.draw()
        return
    
    def verify_move(self, event: mih.MoveEvent) -> None:
        # Used only in speedrun mode
        move = event.move
        if self.game.is_mainline(move):
            # the move is the mainline, so it is correct
            self.game.make_move(move)
            for board_canvas in self.views:
                board_canvas.draw()
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
                    for board_canvas in self.views:
                        board_canvas.draw()
                    if self.game.is_end():
                        self._notify_observers(GameEndEvent())
                    return
        else:
            self._notify_observers(WrongMoveEvent())
            return
