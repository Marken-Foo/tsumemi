from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from tsumemi.src.shogi import rules
from tsumemi.src.shogi.basetypes import Koma
from tsumemi.src.shogi.move import TerminationMove
from tsumemi.src.shogi.notation.move_format import with_same_destination

if TYPE_CHECKING:
    from collections.abc import Iterable
    from tsumemi.src.shogi.move import Move
    from tsumemi.src.shogi.notation.move_format import MoveFormat
    from tsumemi.src.shogi.position import Position
    from tsumemi.src.shogi.square import Square


class AbstractMoveWriter(ABC):
    """Abstract base class for a MoveWriter. Writes shogi moves
    given a Move and Position.
    """

    def __init__(self, move_format: MoveFormat) -> None:
        """Equips the move writer with a move format to follow."""
        self.move_format: MoveFormat = move_format
        self.same_move_format: MoveFormat = with_same_destination(move_format)

    def write_move(self, move: Move, pos: Position, is_same: bool = False) -> str:
        """Writes a shogi move as a string, given the move and the
        position it occurred in. `is_same` specifies if the move is
        to be written as though the prior move had the same
        destination square.
        """
        if move.is_null():
            raise ValueError("Attempting to write notation for a NullMove")
        if isinstance(move, TerminationMove):
            return self.write_termination_move(move)
        if is_same:
            return "".join((func(move, pos, self) for func in self.same_move_format))
        return "".join((func(move, pos, self) for func in self.move_format))

    def needs_disambiguation(self, move: Move, ambiguous_moves: Iterable[Move]) -> bool:
        """Given a move and a list of potentially ambiguous moves
        (same end square), identify if the move needs disambiguation.
        """
        needs_promotion = rules.can_be_promotion(move)
        return any(
            (
                rules.can_be_promotion(amb_move) == needs_promotion
                for amb_move in ambiguous_moves
            )
        )

    @abstractmethod
    def write_termination_move(self, move: TerminationMove) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_koma(self, koma: Koma) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_destination(self, sq: Square) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_same_destination(self, sq: Square) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_disambiguation(self, move: Move, ambiguous_moves: Iterable[Move]) -> str:
        raise NotImplementedError

    def write_movetype(self, move: Move) -> str:
        """Writes whether the given move is a drop, capture, or
        normal move.
        """
        if move.start_sq.is_hand():
            return self.write_drop()
        if move.captured != Koma.NONE:
            return self.write_capture()
        return self.write_simple()

    @abstractmethod
    def write_promotion(self, is_promotion: bool) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_coords(self, sq: Square) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_drop(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_capture(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def write_simple(self) -> str:
        raise NotImplementedError
