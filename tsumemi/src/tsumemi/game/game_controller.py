from __future__ import annotations

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.board_gui.board_canvas as bc
import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.move_input_handler as mih

from tsumemi.src.shogi.game import Game
from tsumemi.src.shogi.move import TerminationMove
from tsumemi.src.tsumemi.game.game_model import GameModel, GameStepEvent, GameUpdateEvent
from tsumemi.src.tsumemi.game.game_nav_btns_view import GameNavButtonsFrame
from tsumemi.src.tsumemi.game.game_navigation_view import NavigableGameFrame
from tsumemi.src.tsumemi.movelist.movelist_controller import MovelistController

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Tuple
    from tsumemi.src.tsumemi import skins
    from tsumemi.src.tsumemi.notation_writer import NotationWriter


class GameEndEvent(evt.Event):
    def __init__(self) -> None:
        evt.Event.__init__(self)
        return


class WrongMoveEvent(evt.Event):
    def __init__(self) -> None:
        evt.Event.__init__(self)
        return


class GameController(evt.Emitter, evt.IObserver):
    def __init__(self, notation_writer: NotationWriter) -> None:
        evt.Emitter.__init__(self)
        evt.IObserver.__init__(self)
        self.game: GameModel = GameModel()
        self.movelist_controller: MovelistController = MovelistController(
            self.game, notation_writer
        )
        self.set_free_mode()
        return

    def make_board_canvas(self,
            parent: tk.Widget,
            skin_settings: skins.SkinSettings
        ) -> bc.BoardCanvas:
        """Creates a BoardCanvas to display the game.
        """
        board_canvas = bc.BoardCanvas(
            parent, self.game.get_position(), skin_settings, bg="white"
        )
        board_canvas.add_callback(
            GameStepEvent, board_canvas.set_and_draw_callback
        )
        board_canvas.add_callback(
            GameUpdateEvent, board_canvas.set_and_draw_callback
        )
        self.game.add_observer(board_canvas)

        move_input_handler = mih.MoveInputHandler(board_canvas)
        move_input_handler.add_observer(self)
        return board_canvas

    def make_navigable_view(self,
            parent: tk.Widget,
            skin_settings: skins.SkinSettings
        ) -> Tuple[NavigableGameFrame, bc.BoardCanvas]:
        nav_game_frame = NavigableGameFrame(parent)
        board_canvas = self.make_board_canvas(nav_game_frame, skin_settings)
        nav_buttons = GameNavButtonsFrame(nav_game_frame)
        nav_buttons.add_command_btn_far_left(self.game.go_to_start)
        nav_buttons.add_command_btn_left(self.game.go_prev_move)
        nav_buttons.add_command_btn_right(self.game.go_next_move)
        nav_buttons.add_command_btn_far_right(self.game.go_to_end)
        nav_game_frame.add_items(board_canvas, nav_buttons)
        return nav_game_frame, board_canvas

    def get_current_sfen(self) -> str:
        return self.game.get_current_sfen()

    def set_game(self, game: Game) -> None:
        self.game.copy_from(game)
        return

    def set_speedrun_mode(self) -> None:
        self.add_callback(mih.MoveEvent, self.verify_move)
        return

    def set_free_mode(self) -> None:
        self.add_callback(mih.MoveEvent, self._add_move)
        return

    def _add_move(self, event: mih.MoveEvent) -> None:
        """Make the move, regardless of whether the move is in the
        game or not.
        """
        move = event.move
        self.game.add_move(move)
        return

    def verify_move(self, event: mih.MoveEvent) -> None:
        # Used only in speedrun mode
        move = event.move
        if self.game.game.is_mainline(move):
            # the move is the mainline, so it is correct
            self.game.make_move(move)
            if self.game.game.is_end():
                self._notify_observers(GameEndEvent())
                return
            response_move = self.game.game.get_mainline_move()
            if isinstance(response_move, TerminationMove):
                self._notify_observers(GameEndEvent())
                return
            self.game.make_move(response_move)
            if self.game.game.is_end():
                self._notify_observers(GameEndEvent())
            return
        self._notify_observers(WrongMoveEvent())
        return
