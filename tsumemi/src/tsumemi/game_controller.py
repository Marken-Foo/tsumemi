from __future__ import annotations

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.board_gui.board_canvas as bc
import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.move_input_handler as mih

from tsumemi.src.shogi.basetypes import TerminationMove
from tsumemi.src.shogi.game import Game
from tsumemi.src.tsumemi.game_navigation_view import NavigableGameFrame

if TYPE_CHECKING:
    import tkinter as tk
    from typing import List, Tuple
    import tsumemi.src.tsumemi.img_handlers as imghand


class GameEndEvent(evt.Event):
    def __init__(self) -> None:
        evt.Event.__init__(self)
        return


class WrongMoveEvent(evt.Event):
    def __init__(self) -> None:
        evt.Event.__init__(self)
        return


class GameController(evt.Emitter, evt.IObserver):
    def __init__(self) -> None:
        evt.Emitter.__init__(self)
        evt.IObserver.__init__(self)
        self.game = Game()
        self.views: List[bc.BoardCanvas] = []
        self.set_free_mode()
        return

    def make_board_canvas(self,
            parent: tk.Widget,
            skin_settings: imghand.SkinSettings,
            *args, **kwargs
        ) -> bc.BoardCanvas:
        """Creates a BoardCanvas to display the game.
        """
        board_canvas = bc.BoardCanvas(parent, self.game, skin_settings,
            bg="white", *args, **kwargs
        )
        move_input_handler = mih.MoveInputHandler(board_canvas)
        move_input_handler.add_observer(self)
        self.views.append(board_canvas)
        return board_canvas

    def make_navigable_view(self,
            parent: tk.Widget,
            skin_settings: imghand.SkinSettings,
            *args, **kwargs
        ) -> Tuple[NavigableGameFrame, bc.BoardCanvas]:
        nav_game_frame = NavigableGameFrame(
            parent, skin_settings, self, *args, **kwargs
        )
        board_canvas = nav_game_frame.board_canvas
        move_input_handler = mih.MoveInputHandler(board_canvas)
        move_input_handler.add_observer(self)
        self.views.append(board_canvas)
        return nav_game_frame, board_canvas

    def get_current_sfen(self) -> str:
        return self.game.get_current_sfen()

    def set_game(self, game: Game) -> None:
        self.game.copy_from(game)
        for board_canvas in self.views:
            board_canvas.set_position(game.position)
        return

    def set_speedrun_mode(self) -> None:
        self.add_callback(mih.MoveEvent, self.verify_move)
        return

    def set_free_mode(self) -> None:
        self.add_callback(mih.MoveEvent, self._add_move)
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
            response_move = self.game.get_mainline_move()
            if isinstance(response_move, TerminationMove):
                self._notify_observers(GameEndEvent())
                return
            self.game.make_move(response_move)
            self.refresh_views()
            if self.game.is_end():
                self._notify_observers(GameEndEvent())
            return
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
