from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules

from tsumemi.src.shogi.basetypes import Koma, Move, Square, SFEN_FROM_KOMA

if TYPE_CHECKING:
    from typing import Iterable, Sequence
    from tsumemi.src.shogi.position import Position
    MoveFormat = Sequence[MoveParts]


class MoveParts(Enum):
    KOMA = 1
    DEST = 2
    DISAMBIG = 3
    MOVETYPE = 4 # utsu is disambiguation in Japanese
    PROMO = 5


WESTERN_MOVE_FORMAT: MoveFormat = (
    MoveParts.KOMA,
    MoveParts.DISAMBIG,
    MoveParts.MOVETYPE,
    MoveParts.DEST,
    MoveParts.PROMO
)


class AbstractMoveWriter(ABC):
    def __init__(self, move_format: MoveFormat) -> None:
        self.move_format: MoveFormat = move_format
        self.aggressive_disambiguation = False
        return
    
    def write_move(self, move: Move, pos: Position) -> str:
        res = []
        ambiguous_moves = rules.get_ambiguous_moves(pos, move)
        needs_promotion = rules.is_promotion_available(move)
        needs_disambiguation = self.needs_disambiguation(move, pos, ambiguous_moves)
            
        for component in self.move_format:
            component_str = ""
            if component == MoveParts.KOMA:
                component_str = self.write_koma(move.koma)
            elif component == MoveParts.DEST:
                component_str = self.write_destination(move.end_sq)
            elif component == MoveParts.DISAMBIG:
                if needs_disambiguation:
                    component_str = self.write_disambiguation(
                        pos, move, ambiguous_moves
                    )
            elif component == MoveParts.MOVETYPE:
                component_str = self.write_movetype(move)
            elif component == MoveParts.PROMO:
                if needs_promotion:
                    component_str = self.write_promotion(move.is_promotion)
            else:
                raise ValueError(f"Unknown move component {component}")
            res.append(component_str)
        return "".join(res)
    
    def needs_disambiguation(self,
            move: Move,
            pos: Position,
            ambiguous_moves: Iterable[Move]
        ) -> bool:
        needs_promotion = rules.is_promotion_available(move)
        if self.aggressive_disambiguation:
            return (
                len(list(ambiguous_moves)) > 1
                and not (needs_promotion and len(list(ambiguous_moves)) == 2)
            )
        else:
            for amb_move in ambiguous_moves:
                if (rules.is_promotion_available(amb_move) == needs_promotion
                        and move.start_sq != amb_move.start_sq
                ):
                    return True
            else:
                return False
    
    @abstractmethod
    def write_koma(self, koma: Koma) -> str:
        raise NotImplementedError
    
    def write_destination(self, sq: Square) -> str:
        return self.write_coords(sq)
    
    @abstractmethod
    def write_disambiguation(self, pos: Position, move: Move, ambiguous_moves: Iterable[Move]) -> str:
        raise NotImplementedError
    
    def write_movetype(self, move) -> str:
        if move.start_sq == Square.HAND:
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


class WesternMoveWriter(AbstractMoveWriter):
    def write_koma(self, koma: Koma) -> str:
        return SFEN_FROM_KOMA[koma].upper()
    
    def write_disambiguation(self, pos: Position, move: Move, ambiguous_moves: Iterable[Move]) -> str:
        start_sq = move.start_sq
        return self.write_coords(start_sq)
    
    def write_promotion(self, is_promotion: bool) -> str:
        return "+" if is_promotion else "="
    
    def write_coords(self, sq: Square) -> str:
        return str(sq)
    
    def write_drop(self) -> str:
        return "*"
    
    def write_capture(self) -> str:
        return "x"
    
    def write_simple(self) -> str:
        return "-"


class JapaneseMoveWriter(AbstractMoveWriter):
    pass


class KitaoKawasakiMoveWriter(AbstractMoveWriter):
    pass


class IrohaMoveWriter(AbstractMoveWriter):
    pass
