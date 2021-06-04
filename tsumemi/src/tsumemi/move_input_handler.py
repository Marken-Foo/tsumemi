from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules
import tsumemi.src.tsumemi.event as evt

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Side, Square

if TYPE_CHECKING:
    from typing import List, Optional, Tuple
    from tsumemi.src.shogi.game import Game
    from tsumemi.src.tsumemi.board_canvas import BoardCanvas


class MoveEvent(evt.Event):
    def __init__(self, move: Move) -> None:
        self.move = move
        return


class MoveInputHandlerState(ABC):
    def __init__(self) -> None:
        return
    
    @abstractmethod
    def receive_input(self, event, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        return
    
    def receive_promotion(self, caller: MoveInputHandler,
            is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        raise RuntimeError("Unexpected promotion input to MoveInputHandler")


class ReadyState(MoveInputHandlerState):
    def receive_input(self, event, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        # "hand"
        if sq == Square.HAND:
            if hand_side == caller.position.turn:
                caller.focused_sq = sq
                caller.focused_ktype = hand_ktype
                caller.board_canvas.set_focus(sq, hand_ktype)
                caller.set_state(HandState())
            else:
                caller.clear_focus()
            return
        koma = caller.position.get_koma(sq)
        if koma == Koma.NONE:
            return
        elif koma.side() == caller.position.turn:
            caller.set_focus(sq)
            caller.set_state(BoardState())
        else: # enemy piece selected
            return


class HandState(MoveInputHandlerState):
    def receive_input(self, event, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        if sq == Square.HAND:
            if hand_side != caller.position.turn:
                caller.clear_focus()
                caller.set_state(ReadyState())
                return
            elif hand_ktype == caller.focused_ktype:
                caller.clear_focus()
                caller.set_state(ReadyState())
                return
            else:
                caller.focused_sq = sq
                caller.focused_ktype = hand_ktype
                caller.board_canvas.set_focus(sq, hand_ktype)
                return
        koma = caller.position.get_koma(sq)
        if koma == Koma.NONE:
            caller.execute_drop(sq)
            # regardless of success, will transition to ReadyState.
            caller.clear_focus()
            caller.set_state(ReadyState())
            return
        elif koma.side() == caller.position.turn:
            caller.set_focus(sq)
            caller.set_state(BoardState())
            return
        else:
            caller.clear_focus()
            caller.set_state(ReadyState())
            return


class BoardState(MoveInputHandlerState):
    def receive_input(self, event, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        if sq == Square.HAND:
            if hand_side == caller.position.turn:
                caller.focused_sq = sq
                caller.focused_ktype = hand_ktype
                caller.board_canvas.set_focus(sq, hand_ktype)
                caller.set_state(HandState())
                return
            else:
                caller.clear_focus()
                caller.set_state(ReadyState())
                return
        koma = caller.position.get_koma(sq)
        if koma == Koma.NONE:
            is_completed = caller.execute_move(sq)
            if is_completed:
                caller.clear_focus()
                caller.set_state(ReadyState())
                return
            else:
                caller.set_state(WaitForPromotionState())
                return
        elif koma.side() == caller.position.turn:
            if sq == caller.focused_sq:
                caller.clear_focus()
                caller.set_state(ReadyState())
                return
            else:
                caller.set_focus(sq)
                return
        else:
            is_completed = caller.execute_move(sq)
            if is_completed:
                caller.clear_focus()
                caller.set_state(ReadyState())
                return
            else:
                caller.set_state(WaitForPromotionState())
                return


class WaitForPromotionState(MoveInputHandlerState):
    def receive_input(self, event, caller: MoveInputHandler,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        return
    
    def receive_promotion(self, caller: MoveInputHandler,
            is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        if is_promotion is None:
            # This means promotion choice is cancelled
            caller.clear_focus()
            caller.set_state(ReadyState())
            return
        else:
            # Promotion choice is made, yes or no
            mv = Move(
                start_sq=caller.focused_sq, end_sq=sq,
                koma=Koma.make(caller.position.turn, ktype),
                captured=caller.position.get_koma(sq),
                is_promotion=is_promotion
            )
            caller.send_move(mv)
            caller.clear_focus()
            caller.set_state(ReadyState())
            return


class MoveInputHandler(evt.Emitter):
    """Handles logic/legality for move input via frontend BoardCanvas.
    Emits MoveEvents when a legal move has been successfully input.
    """
    def __init__(self, board_canvas: BoardCanvas) -> None:
        self.observers: List[evt.IObserver] = []
        self.board_canvas = board_canvas
        self.board_canvas.connect_game_adapter(self)
        self.position = self.board_canvas.game.position
        self.focused_sq = Square.NONE
        self.focused_ktype = KomaType.NONE
        
        self.state: MoveInputHandlerState = ReadyState()
        return
    
    def clear_focus(self) -> None:
        self.focused_sq = Square.NONE
        self.focused_ktype = KomaType.NONE
        self.set_state(ReadyState())
        self.board_canvas.set_focus(Square.NONE)
        return
    
    def set_focus(self, sq: Square) -> None:
        self.focused_sq = sq
        self.focused_ktype = KomaType.get(self.position.get_koma(sq))
        self.board_canvas.set_focus(sq)
        return
    
    def send_move(self, move: Move) -> None:
        self._notify_observers(MoveEvent(move))
        return
    
    def set_state(self, state: MoveInputHandlerState) -> None:
        self.state = state
        return
    
    def execute_drop(self, sq: Square) -> bool:
        # create drop moves then check legality
        exists_valid_move, mvlist = self.check_validity(
            start_sq=self.focused_sq, end_sq=sq,
            ktype=self.focused_ktype
        )
        if exists_valid_move:
            # Given the end square and koma type, if a valid
            # drop exists, it's the only one.
            if rules.is_legal(mvlist[0], self.position):
                self.send_move(mvlist[0])
                return True
        return False
    
    def execute_move(self, sq: Square) -> bool:
        ktype = KomaType.get(self.position.get_koma(self.focused_sq))
        exists_valid_move, mvlist = self.check_validity(
            start_sq=self.focused_sq, end_sq=sq, ktype=ktype
        )
        if exists_valid_move:
            # For normal shogi, either one move (promo or non)
            # or two (choice between promo or non)
            if len(mvlist) == 1:
                if rules.is_legal(mvlist[0], self.position):
                    self.send_move(mvlist[0])
                return True
            elif len(mvlist) == 2:
                # If the promotion is legal, so is the
                # nonpromotion, and vice-versa.
                if rules.is_legal(mvlist[0], self.position):
                    # more info needed, GUI prompts for input
                    self.board_canvas.prompt_promotion(sq, ktype)
                    return False
                else:
                    return True
        return False
    
    def receive_square(self, event,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        self.state.receive_input(event=event, caller=self, sq=sq,
            hand_ktype=hand_ktype, hand_side=hand_side
        )
        return
    '''
    def receive_square(self, event,
            sq: Square, hand_ktype: KomaType = KomaType.NONE,
            hand_side: Side = Side.SENTE
        ) -> None:
        """Receive Square (and/or event) from GUI view, retain the
        information, and decide if it completes a legal move or not.
        """
        # game adapter receives a Square (Event?) from the GUI and
        # decides what to do with it
        koma = self.position.get_koma(sq)
        # Selecting the same square deselects it
        if ((sq == self.focused_sq)
                and ((sq != Square.HAND) or (self.focused_ktype == hand_ktype))
            ):
            self.clear_focus()
            return
        # Selecting a hand piece can never complete a move.
        elif sq == Square.HAND:
            if hand_side == self.position.turn:
                self.focused_sq = sq
                self.focused_ktype = hand_ktype
                self.board_canvas.set_focus(sq, hand_ktype)
            else:
                self.clear_focus()
            return
        # If nothing had previously been selected, a move cannot be
        # completed with the current selection.
        elif self.focused_sq == Square.NONE:
            koma = self.position.get_koma(sq)
            if (koma != Koma.NONE) and (koma != Koma.INVALID):
                if koma.side() == self.position.turn:
                    self.set_focus(sq)
            return
        # If a hand piece had previously been selected, consider if a
        # drop move is legal or not.
        elif self.focused_sq == Square.HAND:
            koma = self.position.get_koma(sq)
            if koma == Koma.NONE:
                # create drop moves then check legality
                exists_valid_move, mvlist = self.check_validity(
                    start_sq=self.focused_sq, end_sq=sq,
                    ktype=self.focused_ktype
                )
                if exists_valid_move:
                    # Given the end square and koma type, if a valid
                    # drop exists, it's the only one.
                    if rules.is_legal(mvlist[0], self.position):
                        self.send_move(mvlist[0])
                    self.clear_focus()
                else:
                    self.clear_focus()
                return
            else: # selected a square with a piece
                if koma.side() == self.position.turn:
                    self.set_focus(sq)
                else:
                    self.clear_focus()
                return
        # Else, a board piece had previously been selected, consider
        # if a piece move is legal or not.
        else:
            ktype = KomaType.get(self.position.get_koma(self.focused_sq))
            exists_valid_move, mvlist = self.check_validity(
                start_sq=self.focused_sq, end_sq=sq, ktype=ktype
            )
            if exists_valid_move:
                # For normal shogi, either one move (promo or non)
                # or two (choice between promo or non)
                if len(mvlist) == 1:
                    if rules.is_legal(mvlist[0], self.position):
                        self.send_move(mvlist[0])
                    self.clear_focus()
                elif len(mvlist) == 2:
                    # If the promotion is legal, so is the
                    # nonpromotion, and vice-versa.
                    if rules.is_legal(mvlist[0], self.position):
                        # more info needed, GUI prompts for input
                        self.board_canvas.prompt_promotion(sq, ktype)
                    else:
                        self.clear_focus()
                    return
            else:
                # Not completing a move, update focus accordingly
                koma_new = self.position.get_koma(sq)
                if koma_new == Koma.NONE:
                    self.clear_focus()
                elif koma_new.side() == self.position.turn:
                    self.set_focus(sq)
                else:
                    self.clear_focus()
            return
    '''
    def execute_promotion_choice(self,
            is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        self.state.receive_promotion(caller=self, is_promotion=is_promotion,
            sq=sq, ktype=ktype
        )
    '''
    def execute_promotion_choice(self,
            is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        if is_promotion is None:
            # This means promotion choice is cancelled
            self.clear_focus()
            return
        else:
            # Promotion choice is made, yes or no
            mv = Move(
                start_sq=self.focused_sq, end_sq=sq,
                koma=Koma.make(self.position.turn, ktype),
                captured=self.position.get_koma(sq),
                is_promotion=is_promotion
            )
            self.send_move(mv)
            self.clear_focus()
        return
    '''
    def check_validity(self,
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
