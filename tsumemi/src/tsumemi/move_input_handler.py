from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules
import tsumemi.src.tsumemi.event as evt

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side
from tsumemi.src.shogi.move import Move
from tsumemi.src.shogi.square import Square

if TYPE_CHECKING:
    from tkinter import Event as tkEvent
    from tsumemi.src.shogi.position import Position
    from tsumemi.src.tsumemi.board_gui.board_canvas import BoardCanvas

logger = logging.getLogger(__name__)


class MoveEvent(evt.Event):
    def __init__(self, move: Move) -> None:
        evt.Event.__init__(self)
        self.move = move


class MoveInputHandler(evt.Emitter):
    """Handles logic/legality for move input via frontend BoardCanvas.
    Emits MoveEvents when a legal move has been successfully input.
    """

    def __init__(self, board_canvas: BoardCanvas) -> None:
        super().__init__()
        self.position: Position
        self.focused_sq = Square.NONE
        self.focused_ktype = KomaType.NONE
        # Move input handling logic uses a state machine.
        self.states: dict[str, MoveInputHandlerState] = {
            "ready": ReadyState(),
            "hand": HandState(),
            "board": BoardState(),
            "wait_for_promotion": WaitForPromotionState(),
            "disabled": DisabledState(),
        }
        self.active_state: MoveInputHandlerState = ReadyState()
        # sync with board canvas
        self.board_canvas = board_canvas
        board_canvas.move_input_handler = self
        self.position = board_canvas.position

    def receive_square(
        self,
        event: tkEvent,
        sq: Square,
        hand_ktype: KomaType = KomaType.NONE,
        hand_side: Side = Side.SENTE,
    ) -> None:
        """Receive a Square and other relevant inputs from GUI. Let
        the state machine handle it.
        """
        try:
            self.active_state.receive_input(
                event=event,
                caller=self,
                sq=sq,
                hand_ktype=hand_ktype,
                hand_side=hand_side,
            )
        except RuntimeError as exc:
            self.set_state("ready")
            logger.warning(exc, exc_info=True)

    def execute_promotion_choice(
        self, is_promotion: bool | None, sq: Square, ktype: KomaType
    ) -> None:
        """Attempt to carry out the promotion choice by delegating to
        the state machine. is_promotion is True if promotion, False if
        not a promotion, and None otherwise (e.g. instead of choosing,
        the move was cancelled instead.)
        """
        self.active_state.receive_promotion(
            caller=self, is_promotion=is_promotion, sq=sq, ktype=ktype
        )

    def enable(self) -> None:
        self.set_state("ready")

    def disable(self) -> None:
        self.set_state("disabled")

    def set_state(
        self, key: str, sq: Square = Square.NONE, hand_ktype: KomaType = KomaType.NONE
    ) -> None:
        """Set the state machine's state and take any actions needed."""
        if (key == "ready") or (key == "disabled"):
            self.focused_sq = Square.NONE
            self.focused_ktype = KomaType.NONE
            self.board_canvas.set_focus(Square.NONE)
        elif key == "hand":
            self.focused_sq = Square.HAND
            self.focused_ktype = hand_ktype
            self.board_canvas.set_focus(sq, hand_ktype)
        elif key == "board":
            self.focused_sq = sq
            self.focused_ktype = KomaType.get(self.position.get_koma(sq))
            self.board_canvas.set_focus(sq)
        # "wait_for_promotion" currently needs no action
        self.active_state = self.states[key]

    def send_move(self, move: Move) -> None:
        self._notify_observers(MoveEvent(move))

    def attempt_drop(self, sq: Square) -> bool:
        move = rules.create_legal_drop_given_square(
            pos=self.position,
            side=self.position.turn,
            ktype=self.focused_ktype,
            end_sq=sq,
        )
        if move.is_null():
            return False
        else:
            self.send_move(move)
            return True

    def attempt_move(self, sq: Square) -> bool | None:
        """Check if a legal move can be made. Returns True and sends
        out the move if it is, False if not.
        Returns None if more information is needed (e.g. choice of
        promotion/nonpromotion.
        """
        mvlist: list[Move] = rules.create_legal_moves_given_squares(
            pos=self.position, start_sq=self.focused_sq, end_sq=sq
        )
        if not mvlist:
            return False
        elif len(mvlist) == 1:
            self.send_move(mvlist[0])
            return True
        elif len(mvlist) == 2:
            # There is a promotion and nonpromotion option.
            # More info needed, GUI prompts for input.
            koma = self.position.get_koma(self.focused_sq)
            self.board_canvas.prompt_promotion(sq, KomaType.get(koma))
            return None
        else:
            raise RuntimeError("Unexpected mvlist length in _attempt_move()")


class MoveInputHandlerState(ABC):
    """Abstract base class for the move input handling state machine."""

    def __init__(self) -> None:
        return

    @abstractmethod
    def receive_input(
        self,
        event: tkEvent,
        caller: MoveInputHandler,
        sq: Square,
        hand_ktype: KomaType = KomaType.NONE,
        hand_side: Side = Side.SENTE,
    ) -> None:
        return

    def receive_promotion(
        self,
        caller: MoveInputHandler,
        is_promotion: bool | None,
        sq: Square,
        ktype: KomaType,
    ) -> None:
        raise RuntimeError("Unexpected promotion input to MoveInputHandler")


class DisabledState(MoveInputHandlerState):
    """The state when the move input handler is to ignore attempts at
    user input.
    """

    def receive_input(
        self,
        event: tkEvent,
        caller: MoveInputHandler,
        sq: Square,
        hand_ktype: KomaType = KomaType.NONE,
        hand_side: Side = Side.SENTE,
    ) -> None:
        return

    def receive_promotion(
        self,
        caller: MoveInputHandler,
        is_promotion: bool | None,
        sq: Square,
        ktype: KomaType,
    ) -> None:
        return


class ReadyState(MoveInputHandlerState):
    """Represents the state where nothing has been selected."""

    def receive_input(
        self,
        event: tkEvent,
        caller: MoveInputHandler,
        sq: Square,
        hand_ktype: KomaType = KomaType.NONE,
        hand_side: Side = Side.SENTE,
    ) -> None:
        if sq == Square.HAND:
            if hand_side == caller.position.turn:
                caller.set_state("hand", sq=sq, hand_ktype=hand_ktype)
                return
            else:
                caller.set_state("ready")
                return
        koma = caller.position.get_koma(sq)
        if koma == Koma.NONE:
            caller.set_state("ready")
        elif koma.side() == caller.position.turn:
            caller.set_state("board", sq)
        else:  # enemy piece selected
            caller.set_state("ready")


class HandState(MoveInputHandlerState):
    """Represents the state where a piece in hand (of the side to
    move) has been selected.
    """

    def receive_input(
        self,
        event: tkEvent,
        caller: MoveInputHandler,
        sq: Square,
        hand_ktype: KomaType = KomaType.NONE,
        hand_side: Side = Side.SENTE,
    ) -> None:
        if sq == Square.HAND:
            if hand_side != caller.position.turn or hand_ktype == caller.focused_ktype:
                caller.set_state("ready")
                return
            else:
                caller.set_state("hand", sq, hand_ktype)
                return
        koma = caller.position.get_koma(sq)
        if koma == Koma.NONE:
            caller.attempt_drop(sq)
            # regardless of success, will transition to ReadyState.
            caller.set_state("ready")
        elif koma.side() == caller.position.turn:
            caller.set_state("board", sq)
        else:
            caller.set_state("ready")


class BoardState(MoveInputHandlerState):
    """Represents the state where a piece on the board (of the side to
    move) has been selected.
    """

    def receive_input(
        self,
        event: tkEvent,
        caller: MoveInputHandler,
        sq: Square,
        hand_ktype: KomaType = KomaType.NONE,
        hand_side: Side = Side.SENTE,
    ) -> None:
        if sq == Square.HAND:
            if hand_side == caller.position.turn:
                caller.set_state("hand", sq, hand_ktype)
                return
            else:
                caller.set_state("ready")
                return
        koma = caller.position.get_koma(sq)
        if koma != Koma.NONE and koma.side() == caller.position.turn:
            if sq == caller.focused_sq:
                caller.set_state("ready")
            else:
                caller.set_state("board", sq)
        else:
            is_completed = caller.attempt_move(sq)
            if is_completed is None:
                caller.set_state("wait_for_promotion")
            else:
                caller.set_state("ready")


class WaitForPromotionState(MoveInputHandlerState):
    """Represents the state where a destination has been selected but
    the choice between promoting and not promoting has not been made.
    """

    def receive_input(
        self,
        event: tkEvent,
        caller: MoveInputHandler,
        sq: Square,
        hand_ktype: KomaType = KomaType.NONE,
        hand_side: Side = Side.SENTE,
    ) -> None:
        if sq == Square.HAND:
            # acts as cancelling the move
            caller.board_canvas.clear_promotion_prompts()
            caller.set_state("ready")
            return
        raise RuntimeError(
            "Unexpected input to MoveInputHandler while waiting for promotion decision"
        )

    def receive_promotion(
        self,
        caller: MoveInputHandler,
        is_promotion: bool | None,
        sq: Square,
        ktype: KomaType,
    ) -> None:
        if is_promotion is None:
            # This means promotion choice is cancelled
            caller.set_state("ready")
        else:
            # Promotion choice is made, yes or no
            move = Move(
                start_sq=caller.focused_sq,
                end_sq=sq,
                koma=Koma.make(caller.position.turn, ktype),
                captured=caller.position.get_koma(sq),
                is_promotion=is_promotion,
            )
            caller.send_move(move)
            caller.set_state("ready")
