from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import tsumemi.src.shogi.rules as rules

from tsumemi.src.shogi.basetypes import Koma, KomaType, TerminationMove
from tsumemi.src.shogi.basetypes import KANJI_NOTATION_FROM_KTYPE, SFEN_FROM_KOMA

if TYPE_CHECKING:
    from typing import Dict, Iterable
    from tsumemi.src.shogi.basetypes import Move, Side, Square
    from tsumemi.src.shogi.position import Position
    MoveFormat = Iterable[MoveNotationBuilder]


class MoveNotationBuilder(ABC):
    def __init__(self) -> None:
        return

    @abstractmethod
    def build(self, move: Move, pos: Position, move_writer: AbstractMoveWriter
        ) -> str:
        raise NotImplementedError


class KomaNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, pos: Position, move_writer: AbstractMoveWriter
        ) -> str:
        return move_writer.write_koma(move.koma)


class DisambiguationNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, pos: Position, move_writer: AbstractMoveWriter
        ) -> str:
        ambiguous_moves = rules.get_ambiguous_moves(pos, move)
        needs_disambiguation = move_writer.needs_disambiguation(
            move, ambiguous_moves
        )
        if needs_disambiguation:
            return move_writer.write_disambiguation(pos, move, ambiguous_moves)
        else:
            return ""


class MovetypeNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, pos: Position, move_writer: AbstractMoveWriter
        ) -> str:
        return move_writer.write_movetype(move)


class DestinationNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, pos: Position, move_writer: AbstractMoveWriter
        ) -> str:
        return move_writer.write_destination(move.end_sq)


class PromotionNotationBuilder(MoveNotationBuilder):
    def build(self, move: Move, pos: Position, move_writer: AbstractMoveWriter
        ) -> str:
        if rules.can_be_promotion(move):
            return move_writer.write_promotion(move.is_promotion)
        else:
            return ""


class AbstractMoveWriter(ABC):
    def __init__(self, move_format: MoveFormat) -> None:
        self.move_format: MoveFormat = move_format
        self.aggressive_disambiguation = False
        return

    def get_new_instance(self) -> AbstractMoveWriter:
        if self.__class__ == AbstractMoveWriter:
            raise NotImplementedError
        return self.__class__(self.move_format)

    def write_move(self,
            move: Move, pos: Position, is_same: bool = False
        ) -> str:
        if move.is_null():
            raise ValueError("Attempting to write notation for a NullMove")
        if isinstance(move, TerminationMove):
            return self.write_termination_move(move)

        res = []
        for builder in self.move_format:
            if isinstance(builder, DestinationNotationBuilder):
                if is_same:
                    res.append(self.write_same_destination(move.end_sq))
                else:
                    res.append(self.write_destination(move.end_sq))
                continue
            res.append(builder.build(move, pos, self))
        return "".join(res)

    def needs_disambiguation(self,
            move: Move, ambiguous_moves: Iterable[Move]
        ) -> bool:
        if self.aggressive_disambiguation:
            return bool(list(ambiguous_moves))
        else:
            needs_promotion = rules.can_be_promotion(move)
            return any((
                rules.can_be_promotion(amb_move) == needs_promotion
                for amb_move in ambiguous_moves
            ))

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
    def write_disambiguation(self, pos: Position, move: Move, ambiguous_moves: Iterable[Move]) -> str:
        raise NotImplementedError

    def write_movetype(self, move) -> str:
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


class WesternMoveWriter(AbstractMoveWriter):
    def write_termination_move(self, move: TerminationMove) -> str:
        return move.to_latin()

    def write_koma(self, koma: Koma) -> str:
        return SFEN_FROM_KOMA[koma].upper()

    def write_destination(self, sq: Square) -> str:
        return self.write_coords(sq)

    def write_same_destination(self, sq: Square) -> str:
        return ""

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


class KitaoKawasakiMoveWriter(WesternMoveWriter):
    def write_koma(self, koma: Koma) -> str:
        return KANJI_NOTATION_FROM_KTYPE[KomaType.get(koma)]

    def write_disambiguation(self,
            pos: Position, move: Move, ambiguous_moves: Iterable[Move]
        ) -> str:
        start_sq = move.start_sq
        return f"({self.write_coords(start_sq)})"


class JapaneseMoveWriter(AbstractMoveWriter):
    def write_termination_move(self, move: TerminationMove) -> str:
        return move.to_ja_kif()

    def write_koma(self, koma: Koma) -> str:
        return KANJI_NOTATION_FROM_KTYPE[KomaType.get(koma)]

    def write_destination(self, sq: Square) -> str:
        return self.write_coords(sq)

    def write_same_destination(self, sq: Square) -> str:
        return "同"

    def write_disambiguation(self,
            pos: Position, move: Move, ambiguous_moves: Iterable[Move]
        ) -> str:
        return _disambiguate_japanese_move(
            pos, move, ambiguous_moves, self.aggressive_disambiguation
        )

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


class IrohaMoveWriter(JapaneseMoveWriter):
    IROHA_SQUARES = (
        "い", "ろ", "は", "に", "ほ", "へ", "と", "ち", "り",
        "ぬ", "る", "を", "わ", "か", "よ", "た", "れ", "そ",
        "つ", "ね", "な", "ら", "む", "う", "の", "く", "や",
        "ま", "け", "ふ", "こ", "え", "て", "あ", "さ", "き",
        "ゆ", "め", "み", "し", "ひ", "も", "せ", "す", "京",
        "一", "三", "五", "六", "七", "八", "十", "百", "千",
        "万", "花", "鳥", "風", "月", "春", "夏", "秋", "冬",
        "柳", "桜", "松", "楓", "雨", "露", "霜", "雪", "山",
        "谷", "川", "海", "里", "村", "森", "竹", "草", "石",
    )

    def write_destination(self, sq: Square) -> str:
        return self.write_coords(sq)

    def write_same_destination(self, sq: Square) -> str:
        return self.write_destination(sq)

    def write_coords(self, sq: Square) -> str:
        return IrohaMoveWriter.IROHA_SQUARES[sq-1]


def _disambiguate_japanese_move(
        pos: Position,
        move: Move,
        ambiguous_moves: Iterable[Move],
        aggressive_disambiguation: bool,
    ) -> str:
    origin_squares = set((
        amb_move.start_sq for amb_move in ambiguous_moves
        if (aggressive_disambiguation)
        or rules.can_be_promotion(amb_move) == rules.can_be_promotion(move)
    ))
    general_pieces = set((
        KomaType.GI, KomaType.KI, KomaType.TO,
        KomaType.NY, KomaType.NK, KomaType.NG
    ))
    side = move.koma.side()
    start_sq = move.start_sq
    end_sq = move.end_sq
    # sugu is special case
    if KomaType.get(move.koma) in general_pieces:
        if end_sq.is_immediately_forward_of(start_sq, side):
            return "直"
    if _is_leftmost(start_sq, origin_squares, side):
        return "左"
    elif _is_rightmost(start_sq, origin_squares, side):
        return "右"
    elif end_sq.is_same_row(start_sq):
        sqs = [sq for sq in origin_squares if end_sq.is_same_row(sq)]
        return _disambiguate_character(start_sq, sqs, side) + "寄"
    elif end_sq.is_forward_of(start_sq, side):
        sqs = []
        for sq in origin_squares:
            if end_sq.is_forward_of(sq, side) and not (
                KomaType.get(move.koma) in general_pieces
                and end_sq.is_immediately_forward_of(sq, side)
            ):
                sqs.append(sq)
        return _disambiguate_character(start_sq, sqs, side) + "上"
    elif end_sq.is_backward_of(start_sq, side):
        sqs = [sq for sq in origin_squares if end_sq.is_backward_of(sq, side)]
        return _disambiguate_character(start_sq, sqs, side) + "引"
    raise ValueError(f"Disambiguation failed unexpectedly on move: {str(move)}")


def _disambiguate_character(
        start_sq: Square, other_sqs: Iterable[Square], side: Side
    ) -> str:
    if not other_sqs:
        return ""
    elif _is_leftmost(start_sq, other_sqs, side):
        return "左"
    elif _is_rightmost(start_sq, other_sqs, side):
        return "右"
    else:
        return "中"


def _is_leftmost(sq: Square, sqs: Iterable[Square], side: Side) -> bool:
    return all((sq.is_left_of(sq_other, side) for sq_other in sqs))


def _is_rightmost(sq: Square, sqs: Iterable[Square], side: Side) -> bool:
    return all((sq.is_right_of(sq_other, side) for sq_other in sqs))



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
