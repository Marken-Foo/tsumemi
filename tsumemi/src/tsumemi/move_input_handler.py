from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules
import tsumemi.src.tsumemi.event as evt

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Side, Square

if TYPE_CHECKING:
    import tkinter.Event as tkEvent
    from typing import Dict, List, Optional, Tuple
    from tsumemi.src.shogi.game import Game
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
    
    def receive_square(self, event: tkEvent,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        """Receive a Square and other relevant inputs from GUI. Let
        the state machine handle it.
        """
        try:
            self.active_state.receive_input(event=event, caller=self, sq=sq,
                hand_ktype=hand_ktype, hand_side=hand_side
            )
        except RuntimeError as e:
            self._set_state("ready")
            logger.warning(e, exc_info=True)
        return
    
    def execute_promotion_choice(self, is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        """Attempt to carry out the promotion choice by delegating to
        the state machine. is_promotion is True if promotion, False if
        not a promotion, and None otherwise (e.g. instead of choosing,
        the move was cancelled instead.)
        """
        self.active_state.receive_promotion(caller=self,
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
        """Send out a move once it has been determined to be legal.
        """
        self._notify_observers(MoveEvent(move))
        return
    
    def _attempt_drop(self, sq: Square) -> bool:
        """Check if a legal drop move can be made.
        """
        # create drop moves then check legality
        exists_valid_move, mvlist = self._check_validity(
            start_sq=self.focused_sq, end_sq=sq,
            ktype=self.focused_ktype
        )
        if exists_valid_move:
            # Given the end square and koma type, if a valid
            # drop exists, it's the only one.
            if rules.is_legal(mvlist[0], self.position):
                self._send_move(mvlist[0])
                return True
        return False
    
    def _attempt_move(self, sq: Square) -> Optional[bool]:
        """Check if a legal move can be made. Returns None if more
        information is needed (e.g. choice of promotion/nonpromotion.
        """
        ktype = KomaType.get(self.position.get_koma(self.focused_sq))
        exists_valid_move, mvlist = self._check_validity(
            start_sq=self.focused_sq, end_sq=sq, ktype=ktype
        )
        if exists_valid_move:
            # For normal shogi, either one move (promo or non)
            # or two (choice between promo or non)
            if len(mvlist) == 1:
                if rules.is_legal(mvlist[0], self.position):
                    self._send_move(mvlist[0])
                return True
            elif len(mvlist) == 2:
                # If the promotion is legal, so is the
                # nonpromotion, and vice-versa.
                if rules.is_legal(mvlist[0], self.position):
                    # more info needed, GUI prompts for input
                    self.board_canvas.prompt_promotion(sq, ktype)
                    return None
                else:
                    return True
        return False
    
    def _check_validity(self,
            start_sq: Square, end_sq: Square,
            ktype: KomaType = KomaType.NONE
        ) -> Tuple[bool, List[Move]]:
        """Decide if there exists a valid move given the start and
        end Squares, and KomaType (needed for hand pieces).
        """
        res_bool = False
        if start_sq == Square.HAND:
            mvlist = rules.generate_drop_moves(
                pos=self.position, side=self.position.turn, ktype=ktype
            )
            mvlist_filtered = [mv for mv in mvlist if (mv.end_sq == end_sq)]
            if len(mvlist_filtered) == 1:
                res_bool = True
            return res_bool, mvlist_filtered
        # Now start_sq should be a valid Square on the board
        koma = self.position.get_koma(start_sq)
        if koma.side() == self.position.turn:
            ktype = KomaType.get(koma)
            mvlist = rules.generate_valid_moves(
                pos=self.position, side=self.position.turn, ktype=ktype
            )
            mvlist_filtered = [
                mv for mv in mvlist
                if (mv.start_sq == start_sq) and (mv.end_sq == end_sq)
            ]
            if (len(mvlist_filtered) == 1) or (len(mvlist_filtered) == 2):
                res_bool = True
            return res_bool, mvlist_filtered
        return False, []


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
            if is_completed:
                caller._set_state("ready")
                return
            else:
                caller._set_state("wait_for_promotion")
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
