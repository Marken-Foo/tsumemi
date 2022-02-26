from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Side, Square
from tsumemi.src.shogi.basetypes import KANJI_NOTATION_FROM_KTYPE, SFEN_FROM_KOMA

if TYPE_CHECKING:
    from typing import Iterable, Tuple
    from tsumemi.src.shogi.position import Position
    MoveFormat = Iterable[MoveNotationBuilder]


class MoveNotationBuilder(ABC):
    def __init__(self) -> None:
        return
    
    @abstractmethod
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        raise NotImplementedError


class KomaNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_koma(move.koma)


class DisambiguationNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        raise RuntimeError("Builder not responsible for notation disambiguation")


class MovetypeNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_movetype(move)


class DestinationNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_destination(move.end_sq)


class PromotionNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, move_writer: AbstractMoveWriter) -> str:
        return move_writer.write_promotion(move.is_promotion)


WESTERN_MOVE_FORMAT: MoveFormat = (
    KomaNotationBuilder(),
    DisambiguationNotationBuilder(),
    MovetypeNotationBuilder(),
    DestinationNotationBuilder(),
    PromotionNotationBuilder(),
)


JAPANESE_MOVE_FORMAT: MoveFormat = (
    DestinationNotationBuilder(),
    KomaNotationBuilder(),
    MovetypeNotationBuilder(),
    DisambiguationNotationBuilder(),
    PromotionNotationBuilder(),
)


class AbstractMoveWriter(ABC):
    def __init__(self, move_format: MoveFormat) -> None:
        self.move_format: MoveFormat = move_format
        self.aggressive_disambiguation = True
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
    
    def write_disambiguation(self,
            pos: Position, move: Move, ambiguous_moves: Iterable[Move]
        ) -> str:
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
    def write_koma(self, koma: Koma) -> str:
        return KANJI_NOTATION_FROM_KTYPE[KomaType.get(koma)]
    
    def write_disambiguation(self,
            pos: Position, move: Move, ambiguous_moves: Iterable[Move]
        ) -> str:
        origin_squares = set((
            amb_move.start_sq for amb_move in ambiguous_moves
            if (self.aggressive_disambiguation) or rules.can_promote(amb_move) == rules.can_promote(move)
        ))
        general_pieces = set((
            KomaType.GI, KomaType.KI, KomaType.TO,
            KomaType.NY, KomaType.NK, KomaType.NG
        ))
        koma = move.koma
        side = koma.side()
        start_sq = move.start_sq
        end_sq = move.end_sq
        start_col, start_row = start_sq.get_cr()
        end_col, end_row = end_sq.get_cr()
        # sugu is special case
        if KomaType.get(koma) in general_pieces:
            forward = -1 if side == Side.SENTE else 1
            if start_col == end_col and start_row + forward == end_row:
                return "直"
        # sayuu is left/rightmost
        if self.is_leftmost(start_sq, origin_squares, side):
            return "左"
        elif self.is_rightmost(start_sq, origin_squares, side):
            return "右"
        # yori if same rank; sayuu if not unique
        if start_row == end_row:
            for sq in origin_squares:
                _, row = sq.get_cr()
                if row == end_row:
                    return "左寄" if self.is_left_of(start_sq, sq, side) else "右寄"
            else: # for-else loop
                return "寄"
        # hiki if falling back; sayuu if not unique
        if self.is_forward_of(start_sq, end_sq, side):
            for sq in origin_squares:
                if self.is_forward_of(sq, end_sq, side):
                    return "左引" if self.is_left_of(start_sq, sq, side) else "右引"
            else: # for-else loop
                return "引"
        # agaru if rising; sayuu if not unique
        if self.is_forward_of(end_sq, start_sq, side):
            for sq in origin_squares:
                if self.is_forward_of(end_sq, sq, side):
                    return "左上" if self.is_left_of(start_sq, sq, side) else "右上"
            else: # for-else loop
                return "上"
        return self.write_coords(start_sq)
    
    def _subtract_squares(self, sq1: Square, sq2: Square) -> Tuple[int, int]:
        col1, row1 = sq1.get_cr()
        col2, row2 = sq2.get_cr()
        return (col1 - col2, row1 - row2)
    
    def is_left_of(self, sq1: Square, sq2: Square, side: Side) -> bool:
        col_diff, _ = self._subtract_squares(sq1, sq2)
        return (col_diff > 0) if side == Side.SENTE else (col_diff < 0)
    
    def is_right_of(self, sq1: Square, sq2: Square, side: Side) -> bool:
        return self.is_left_of(sq1, sq2, side.switch())
    
    def is_forward_of(self, sq1: Square, sq2: Square, side: Side) -> bool:
        _, row_diff = self._subtract_squares(sq1, sq2)
        return row_diff < 0 if side == Side.SENTE else row_diff > 0
    
    def is_leftmost(self, sq: Square, sqs: Iterable[Square], side: Side) -> bool:
        return all((self.is_left_of(sq, comp_sq, side) for comp_sq in sqs))
    
    def is_rightmost(self, sq: Square, sqs: Iterable[Square], side: Side) -> bool:
        return all((self.is_right_of(sq, comp_sq, side) for comp_sq in sqs))
    
    def write_promotion(self, is_promotion: bool) -> str:
        return "成" if is_promotion else "不成"
    
    def write_coords(self, sq: Square) -> str:
        return sq.to_japanese()
    
    def write_drop(self) -> str:
        return "打"
    
    def write_capture(self) -> str:
        return ""
    
    def write_simple(self) -> str:
        return ""


class KitaoKawasakiMoveWriter(AbstractMoveWriter):
    pass


class IrohaMoveWriter(AbstractMoveWriter):
    pass
