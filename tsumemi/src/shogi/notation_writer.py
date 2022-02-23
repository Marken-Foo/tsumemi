from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Square, SFEN_FROM_KOMA
from tsumemi.src.shogi.position import Position

if TYPE_CHECKING:
    from typing import Iterable, Sequence
    from tsumemi.src.shogi.basetypes import Side
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
        # self.aggressive_disambiguation = True
        return
    
    def write_move(self, move: Move, pos: Position) -> str:
        res = []
        ambiguous_moves = self.get_ambiguous_moves(move, pos)
        for amb_move in ambiguous_moves:
            if ((amb_move.start_sq == move.start_sq)
                and (amb_move.end_sq == move.end_sq)
                and (amb_move.is_promotion != move.is_promotion)
            ):
                needs_promotion = True
                break
        else:
            needs_promotion = False
        needs_disambiguation = (
            len(list(ambiguous_moves)) > 1
            and not (needs_promotion and len(list(ambiguous_moves)) == 2)
        )
        
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
    
    def get_ambiguous_moves(self, move: Move, pos: Position) -> Iterable[Move]:
        side: Side = move.side
        ktype: KomaType = KomaType.get(move.koma)
        end_sq: Square = move.end_sq
        res = rules.get_ambiguous_moves(pos, move)
        return res
    
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
