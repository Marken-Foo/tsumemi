from __future__ import annotations

import functools

import tsumemi.src.shogi.destination_generation as destgen

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, NullMove, Side, Square
from tsumemi.src.shogi.basetypes import HAND_TYPES, KOMA_TYPES
from tsumemi.src.shogi.position_internals import MailboxBoard

if TYPE_CHECKING:
    from typing import Iterable
    from typing import Any, Callable, Dict, List, Tuple, Union
    from tsumemi.src.shogi.position import Position
    DestGen = Callable[[MailboxBoard, int, Side], List[int]]
    PromConstrTuple = Union[Tuple[bool], Tuple[bool, bool]]
    PromConstr = Callable[[Side, Square, Square], PromConstrTuple]


def create_legal_moves_given_squares(
        pos: Position, start_sq: Square, end_sq: Square
    ) -> List[Move]:
    mvlist = create_valid_moves_given_squares(pos, start_sq, end_sq)
    return [move for move in mvlist if is_legal(move, pos)]

def create_valid_moves_given_squares(
        pos: Position, start_sq: Square, end_sq: Square
    ) -> List[Move]:
    if not exists_valid_move_given_squares(pos, start_sq, end_sq):
        return []
    koma = pos.get_koma(start_sq)
    ktype = KomaType.get(koma)
    side = koma.side()
    _, promotion_constrainer = MOVEGEN_FUNCTIONS[ktype]
    return [
        pos.create_move(start_sq, end_sq, can_promote)
        for can_promote in promotion_constrainer(side, start_sq, end_sq)
    ]

def exists_valid_move_given_squares(
        pos: Position, start_sq: Square, end_sq: Square
    ) -> bool:
    if start_sq == Square.HAND:
        raise ValueError(f"expected non-drop; got {start_sq}, {end_sq}")
    koma = pos.get_koma(start_sq)
    if koma == Koma.NONE or koma == Koma.INVALID:
        return False
    if koma.side() != pos.turn:
        return False
    ktype = KomaType.get(koma)
    board = pos.board
    side = koma.side()
    start_idx = MailboxBoard.sq_to_idx(start_sq)
    end_idx = MailboxBoard.sq_to_idx(end_sq)
    dest_generator, _ = MOVEGEN_FUNCTIONS[ktype]
    destinations = destgen.filter_for_valid_dests(
        dest_generator(board, start_idx, side), board
    )
    return True if end_idx in destinations else False

def create_legal_drop_given_square(
        pos: Position, side: Side, ktype: KomaType, end_sq: Square
    ) -> Move:
    move = create_valid_drop_given_square(pos, side, ktype, end_sq)
    if move.is_null():
        return move
    elif is_legal(move, pos):
        return move
    else:
        return NullMove()

def create_valid_drop_given_square(
        pos: Position, side: Side, ktype: KomaType, end_sq: Square
    ) -> Move:
    if exists_valid_drop_given_square(pos, side, ktype, end_sq):
        return _create_drop_move(side, ktype, end_sq)
    else:
        return NullMove()

def exists_valid_drop_given_square(
        pos: Position, side: Side, ktype: KomaType, end_sq: Square
    ) -> bool:
    if not _is_drop_available(pos, side, ktype):
        return False
    if _is_drop_innately_illegal(pos, side, ktype, end_sq):
        return False
    return True

def is_legal(mv: Move, pos: Position) -> bool:
    side = pos.turn
    pos.make_move(mv)
    ans = not is_in_check(pos, side)
    pos.unmake_move(mv)
    return ans

def is_in_check(pos: Position, side: Side) -> bool:
    # assumes royal king(s)
    king = Koma.make(side, KomaType.OU)
    king_pos = [
        MailboxBoard.idx_to_sq(idx)
        for idx in pos.board.koma_sets[king]
    ]
    for ktype in KOMA_TYPES:
        mvlist = generate_valid_moves(pos, side.switch(), ktype)
        for mv in mvlist:
            if mv.end_sq in king_pos:
                return True
    return False

def _create_drop_move(side: Side, ktype: KomaType, end_sq: Square) -> Move:
    return Move(
        start_sq=Square.HAND,
        end_sq=end_sq,
        koma=Koma.make(side, ktype)
    )

def _idxs_to_squares(idxs: Iterable[int]) -> Iterable[Square]:
    return (MailboxBoard.idx_to_sq(idx) for idx in idxs)

def generate_valid_moves(
        pos: Position, side: Side, ktype: KomaType
    ) -> List[Move]:
    dest_generator, promotion_constrainer = MOVEGEN_FUNCTIONS[ktype]
    mvlist = []
    board = pos.board
    locations = board.koma_sets[Koma.make(side, ktype)]
    for start_idx in locations:
        destinations = destgen.filter_for_valid_dests(
            dest_generator(board, start_idx, side), board
        )
        start_sq = MailboxBoard.idx_to_sq(start_idx)
        destination_sqs = _idxs_to_squares(destinations)
        for end_sq in destination_sqs:
            for can_promote in promotion_constrainer(side, start_sq, end_sq):
                move = pos.create_move(start_sq, end_sq, can_promote)
                mvlist.append(move)
    return mvlist

def generate_drop_moves(
        pos: Position, side: Side, ktype: KomaType
    ) -> List[Move]:
    if not _is_drop_available(pos, side, ktype):
        return []
    empty_sqs = _idxs_to_squares(pos.board.empty_idxs)
    return [
        _create_drop_move(side, ktype, end_sq) for end_sq in empty_sqs
        if not _is_drop_innately_illegal(pos, side, ktype, end_sq)
    ]

def _is_drop_available(pos: Position, side: Side, ktype: KomaType):
    if ktype not in HAND_TYPES:
        raise ValueError(f"{ktype} is not a valid KomaType for a drop move")
    return pos.get_hand_koma_count(side, ktype) != 0

def _is_drop_innately_illegal(
        pos: Position,
        side: Side,
        ktype: KomaType,
        end_sq: Square
    ) -> bool:
    if pos.get_koma(end_sq) != Koma.NONE:
        return True
    if ktype == KomaType.FU:
        if (_is_drop_illegal_ky(side, end_sq)
            or _is_drop_nifu(pos.board, side, end_sq)):
            return True
    elif ktype == KomaType.KY:
        if _is_drop_illegal_ky(side, end_sq):
            return True
    elif ktype == KomaType.KE:
        if _is_drop_illegal_ke(side, end_sq):
            return True
    return False

def _is_drop_nifu(board: MailboxBoard, side: Side, end_sq: Square) -> bool:
    col_num, _ = end_sq.get_cr()
    koma_fu = Koma.make(side, KomaType.FU)
    for row_num in range(1, 10, 1):
        idx = MailboxBoard.cr_to_idx(col_num, row_num)
        if board.mailbox[idx] == koma_fu:
            return True
    return False

def _is_drop_illegal_ky(side: Side, end_sq: Square) -> bool:
    return MailboxBoard.is_sq_in_last_row(end_sq, side)

def _is_drop_illegal_ke(side: Side, end_sq: Square) -> bool:
    return MailboxBoard.is_sq_in_last_two_rows(end_sq, side)


# === Promotion constrainers.
# They determine if there are promotion and/or nonpromotion moves
# given the piece type and the start and end squares.

def constrain_promotions_ky(
        side: Side, start_sq: Square, end_sq: Square
    ) -> PromConstrTuple:
    must_promote = MailboxBoard.is_sq_in_last_row(end_sq, side)
    can_promote = MailboxBoard.is_sq_in_promotion_zone(end_sq, side)
    if must_promote:
        return (True,)
    elif can_promote:
        return (True, False)
    else:
        return (False,)

def constrain_promotions_ke(
        side: Side, start_sq: Square, end_sq: Square
    ) -> PromConstrTuple:
    must_promote = MailboxBoard.is_sq_in_last_two_rows(end_sq, side)
    can_promote = MailboxBoard.is_sq_in_promotion_zone(end_sq, side)
    if must_promote:
        return (True,)
    elif can_promote:
        return (True, False)
    else:
        return (False,)

def constrain_promotable(
        side: Side, start_sq: Square, end_sq: Square
    ) -> PromConstrTuple:
    """Identify promotion and non-promotion moves for pieces that
    are not forced to promote and can move in and out of the
    promotion zone.
    """
    can_promote = (
        MailboxBoard.is_sq_in_promotion_zone(start_sq, side)
        or MailboxBoard.is_sq_in_promotion_zone(end_sq, side)
    )
    if can_promote:
        return (True, False)
    else:
        return (False,)

def constrain_unpromotable(
        side: Side, start_sq: Square, end_sq: Square
    ) -> PromConstrTuple:
    """Identify promotion and non-promotion moves for pieces that
    cannot promote.
    """
    return (False,)

# Contains the functions to generate valid moves for each KomaType.
MOVEGEN_FUNCTIONS: Dict[KomaType, Tuple[DestGen, PromConstr]] = {
    KomaType.FU: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_fu),
        constrain_promotions_ky
    ),
    KomaType.KY: (destgen.generate_dests_ky, constrain_promotions_ky),
    KomaType.KE: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_ke),
        constrain_promotions_ke
    ),
    KomaType.GI: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_gi),
        constrain_promotable
    ),
    KomaType.KI: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_ki),
        constrain_unpromotable
    ),
    KomaType.KA: (destgen.generate_dests_ka, constrain_promotable),
    KomaType.HI: (destgen.generate_dests_hi, constrain_promotable),
    KomaType.OU: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_ou),
        constrain_unpromotable
    ),
    KomaType.TO: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_ki),
        constrain_unpromotable
    ),
    KomaType.NY: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_ki),
        constrain_unpromotable
    ),
    KomaType.NK: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_ki),
        constrain_unpromotable
    ),
    KomaType.NG: (
        functools.partial(destgen.generate_dests_steps, steps=destgen.steps_ki),
        constrain_unpromotable
    ),
    KomaType.UM: (destgen.generate_dests_um, constrain_unpromotable),
    KomaType.RY: (destgen.generate_dests_ry, constrain_unpromotable),
}