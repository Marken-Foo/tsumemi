from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules
import tsumemi.src.tsumemi.event as evt

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Side, Square

if TYPE_CHECKING:
    import tkinter.Event as tkEvent
    from typing import Dict, List, Optional
    from tsumemi.src.shogi.position import Position
    from tsumemi.src.tsumemi.board_canvas import BoardCanvas

logger = logging.getLogger(__name__)


class MoveEvent(evt.Event):
    def __init__(self, move: Move) -> None:
        self.move = move
        return


class MoveInputHandler(evt.Emitter):
    """Handles logic/legality for move input via frontend BoardCanvas.
    Emits MoveEvents when a legal move has been successfully input.
    """
    def __init__(self, board_canvas: BoardCanvas) -> None:
        self.observers: List[evt.IObserver] = []
        self.position: Position
        self.focused_sq = Square.NONE
        self.focused_ktype = KomaType.NONE
        # Move input handling logic uses a state machine.
        self.states: Dict[str, MoveInputHandlerState] = {
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
        return
    
    def receive_square(self,
            event: tkEvent,
            sq: Square,
            hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        """Receive a Square and other relevant inputs from GUI. Let
        the state machine handle it.
        """
        try:
            self.active_state.receive_input(
                event=event, caller=self,
                sq=sq, hand_ktype=hand_ktype, hand_side=hand_side
            )
        except RuntimeError as e:
            self._set_state("ready")
            logger.warning(e, exc_info=True)
        return
    
    def execute_promotion_choice(self,
            is_promotion: Optional[bool],
            sq: Square,
            ktype: KomaType
        ) -> None:
        """Attempt to carry out the promotion choice by delegating to
        the state machine. is_promotion is True if promotion, False if
        not a promotion, and None otherwise (e.g. instead of choosing,
        the move was cancelled instead.)
        """
        self.active_state.receive_promotion(
            caller=self,
            is_promotion=is_promotion, sq=sq, ktype=ktype
        )
        return
    
    def enable(self) -> None:
        self._set_state("ready")
        return
    
    def disable(self) -> None:
        self._set_state("disabled")
        return
    
    def _set_state(self, key: str,
            sq: Square = Square.NONE,
            hand_ktype: KomaType = KomaType.NONE
        ) -> None:
        """Set the state machine's state and take any actions needed.
        """
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
        return
    
    def _send_move(self, move: Move) -> None:
        self._notify_observers(MoveEvent(move))
        return
    
    def _attempt_drop(self, sq: Square) -> bool:
        move = rules.create_legal_drop_given_square(
            pos=self.position,
            side=self.position.turn,
            ktype=self.focused_ktype,
            end_sq=sq
        )
        if move.is_null():
            return False
        else:
            self._send_move(move)
            return True
    
    def _attempt_move(self, sq: Square) -> Optional[bool]:
        """Check if a legal move can be made. Returns True and sends
        out the move if it is, False if not.
        Returns None if more information is needed (e.g. choice of promotion/nonpromotion.
        """
        mvlist: List[Move] = rules.create_legal_moves_given_squares(
            pos=self.position,
            start_sq=self.focused_sq,
            end_sq=sq
        )
        if not mvlist:
            return False
        elif len(mvlist) == 1:
            self._send_move(mvlist[0])
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
    """Abstract base class for the move input handling state machine.
    """
    def __init__(self) -> None:
        return
    
    @abstractmethod
    def receive_input(self, event: tkEvent, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        return
    
    def receive_promotion(self, caller: MoveInputHandler,
            is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        raise RuntimeError("Unexpected promotion input to MoveInputHandler")


class DisabledState(MoveInputHandlerState):
    """The state when the move input handler is to ignore attempts at
    user input.
    """
    def receive_input(self, event: tkEvent, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        return
    
    def receive_promotion(self, caller: MoveInputHandler,
            is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        return


class ReadyState(MoveInputHandlerState):
    """Represents the state where nothing has been selected.
    """
    def receive_input(self, event: tkEvent, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        if sq == Square.HAND:
            if hand_side == caller.position.turn:
                caller._set_state("hand", sq=sq, hand_ktype=hand_ktype)
                return
            else:
                caller._set_state("ready")
                return
        koma = caller.position.get_koma(sq)
        if koma == Koma.NONE:
            caller._set_state("ready")
            return
        elif koma.side() == caller.position.turn:
            caller._set_state("board", sq)
            return
        else: # enemy piece selected
            caller._set_state("ready")
            return


class HandState(MoveInputHandlerState):
    """Represents the state where a piece in hand (of the side to
    move) has been selected.
    """
    def receive_input(self, event: tkEvent, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        if sq == Square.HAND:
            if hand_side != caller.position.turn:
                caller._set_state("ready")
                return
            elif hand_ktype == caller.focused_ktype:
                caller._set_state("ready")
                return
            else:
                caller._set_state("hand", sq, hand_ktype)
                return
        koma = caller.position.get_koma(sq)
        if koma == Koma.NONE:
            caller._attempt_drop(sq)
            # regardless of success, will transition to ReadyState.
            caller._set_state("ready")
            return
        elif koma.side() == caller.position.turn:
            caller._set_state("board", sq)
            return
        else:
            caller._set_state("ready")
            return


class BoardState(MoveInputHandlerState):
    """Represents the state where a piece on the board (of the side to
    move) has been selected.
    """
    def receive_input(self, event: tkEvent, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        if sq == Square.HAND:
            if hand_side == caller.position.turn:
                caller._set_state("hand", sq, hand_ktype)
                return
            else:
                caller._set_state("ready")
                return
        koma = caller.position.get_koma(sq)
        if koma == Koma.NONE:
            is_completed = caller._attempt_move(sq)
            if is_completed is None:
                # waiting for promotion
                caller._set_state("wait_for_promotion")
                return
            else:
                caller._set_state("ready")
                return
        elif koma.side() == caller.position.turn:
            if sq == caller.focused_sq:
                caller._set_state("ready")
                return
            else:
                caller._set_state("board", sq)
                return
        else:
            is_completed = caller._attempt_move(sq)
            if is_completed is None:
                caller._set_state("wait_for_promotion")
                return
            else:
                caller._set_state("ready")
                return


class WaitForPromotionState(MoveInputHandlerState):
    """Represents the state where a destination has been selected but
    the choice between promoting and not promoting has not been made.
    """
    def receive_input(self, event: tkEvent, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        if sq == Square.HAND:
            # acts as cancelling the move
            caller.board_canvas.clear_promotion_prompts()
            caller._set_state("ready")
            return
        raise RuntimeError("Unexpected input to MoveInputHandler while waiting "
            "for promotion decision"
        )
    
    def receive_promotion(self, caller: MoveInputHandler,
            is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        if is_promotion is None:
            # This means promotion choice is cancelled
            caller._set_state("ready")
            return
        else:
            # Promotion choice is made, yes or no
            mv = Move(
                start_sq=caller.focused_sq, end_sq=sq,
                koma=Koma.make(caller.position.turn, ktype),
                captured=caller.position.get_koma(sq),
                is_promotion=is_promotion
            )
            caller._send_move(mv)
            caller._set_state("ready")
            return
