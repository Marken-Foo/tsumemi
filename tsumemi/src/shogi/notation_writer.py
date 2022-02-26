from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules

from tsumemi.src.shogi.basetypes import Koma, Move, Square, SFEN_FROM_KOMA

if TYPE_CHECKING:
    from typing import Iterable
    from tsumemi.src.shogi.position import Position
    MoveFormat = Iterable[MoveNotationBuilder]


class MoveNotationBuilder(ABC):
    def __init__(self) -> None:
        return
    
    @abstractmethod
    def build(self, move_writer: AbstractMoveWriter) -> MoveNotationBuilder:
        raise NotImplementedError


class KomaNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_koma(move.koma)


class DisambiguationNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_disambiguation(move)


class MovetypeNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_movetype(move)


class DestinationNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_destination(move.end_sq)


class PromotionNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_promotion(move.is_promotion)


WESTERN_MOVE_FORMAT = (
    KomaNotationBuilder(),
    DisambiguationNotationBuilder(),
    MovetypeNotationBuilder(),
    DestinationNotationBuilder(),
    PromotionNotationBuilder(),
)


class AbstractMoveWriter(ABC):
    def __init__(self, move_format: MoveFormat) -> None:
        self.move_format: MoveFormat = move_format
        self.aggressive_disambiguation = False
        return
    
    def write_move(self, move: Move, pos: Position) -> str:
        res = []
        needs_promotion = rules.can_promote(move)
        ambiguous_moves = rules.get_ambiguous_moves(pos, move)
        needs_disambiguation = self.needs_disambiguation(move, ambiguous_moves)
        
        for builder in self.move_format:
            if isinstance(builder, PromotionNotationBuilder):
                if not needs_promotion:
                    continue
            elif isinstance(builder, DisambiguationNotationBuilder):
                if needs_disambiguation:
                    res.append(self.write_disambiguation(
                        pos, move, ambiguous_moves
                    ))
                continue
            res.append(builder.build(move, self))
        return "".join(res)
    
    def needs_disambiguation(self,
            move: Move, ambiguous_moves: Iterable[Move]
        ) -> bool:
        needs_promotion = rules.can_promote(move)
        if self.aggressive_disambiguation:
            return bool(list(ambiguous_moves))
        else:
            return any((
                rules.can_promote(amb_move) == needs_promotion
                for amb_move in ambiguous_moves
            ))
    
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
