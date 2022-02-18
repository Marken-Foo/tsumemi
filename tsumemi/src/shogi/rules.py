from __future__ import annotations

import functools

import tsumemi.src.shogi.destination_generation as destgen

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, NullMove, Side, Square
from tsumemi.src.shogi.basetypes import HAND_TYPES, KOMA_TYPES
from tsumemi.src.shogi.position_internals import BoardRepresentation

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Tuple
    from tsumemi.src.shogi.position import Position
    DestGen = Callable[[BoardRepresentation, int, Side], List[int]]
    PromConstr = Callable[[Side, int, int], List[Tuple[int, int, bool]]]


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
        BoardRepresentation.idx_to_sq(idx)
        for idx in pos.board.koma_sets[king]
    ]
    for ktype in KOMA_TYPES:
        mvlist = generate_valid_moves(pos, side.switch(), ktype)
        for mv in mvlist:
            if mv.end_sq in king_pos:
                return True
    return False

def generate_legal_moves(pos: Position) -> List[Move]:
    pass

def generate_valid_moves(
        pos: Position, side: Side, ktype: KomaType
    ) -> List[Move]:
    dest_generator, promotion_constrainer = MOVEGEN_FUNCTIONS[ktype]
    mvlist = []
    board = pos.board
    locations = board.koma_sets[Koma.make(side, ktype)]
    for start_idx in locations:
        destinations = dest_generator(board, start_idx, side)
        filtered_dests = [
            idx for idx in destinations if board.mailbox[idx] != Koma.INVALID
        ]
        for end_idx in filtered_dests:
            tuplist = promotion_constrainer(side, start_idx, end_idx)
            for tup in tuplist:
                start, end, promo = tup
                move = _move(board, start, end, side, ktype, promo)
                mvlist.append(move)
    return mvlist

def _move(
        board: BoardRepresentation,
        start_idx: int,
        end_idx: int,
        side: Side,
        ktype: KomaType,
        is_promotion=False
    ) -> Move:
    return Move(
        start_sq=BoardRepresentation.idx_to_sq(start_idx),
        end_sq=BoardRepresentation.idx_to_sq(end_idx),
        koma=Koma.make(side, ktype),
        captured=board.mailbox[end_idx],
        is_promotion=is_promotion
    )

def generate_drop_moves(
        pos: Position, side: Side, ktype: KomaType
    ) -> List[Move]:
    if ktype not in HAND_TYPES:
        return []
    mvlist: List[Move] = []
    if pos.get_hand_koma_count(side, ktype) == 0:
        return mvlist
    board = pos.board
    for end_idx in board.empty_idxs:
        move = create_valid_drop_from_idx(board, side, ktype, end_idx)
        if not move.is_null():
            mvlist.append(move)
    return mvlist

def create_valid_drop_from_idx(
        board: BoardRepresentation,
        side: Side,
        ktype: KomaType,
        end_idx: int
    ) -> Move:
    if ktype == KomaType.FU:
        if is_drop_illegal_ky(side, end_idx):
            return NullMove()
        if is_drop_nifu(board, side, end_idx):
            return NullMove()
    elif ktype == KomaType.KY:
        if is_drop_illegal_ky(side, end_idx):
            return NullMove()
    elif ktype == KomaType.KE:
        if is_drop_illegal_ke(side, end_idx):
            return NullMove()
    return _drop(side, ktype, end_idx)

def is_drop_nifu(board: BoardRepresentation, side: Side, end_idx: int) -> bool:
    col_num = BoardRepresentation.idx_to_c(end_idx)
    for row_num in range(1, 10, 1):
        idx = BoardRepresentation.cr_to_idx(col_num, row_num)
        if board.mailbox[idx] == Koma.make(side, KomaType.FU):
            return True
    return False

def is_drop_illegal_ky(side: Side, end_idx: int) -> bool:
    row_num = BoardRepresentation.idx_to_r(end_idx)
    return (
        ((side == Side.SENTE) and (row_num == 1))
        or ((side == Side.GOTE) and (row_num == 9))
    )

def is_drop_illegal_ke(side: Side, end_idx: int) -> bool:
    row_num = BoardRepresentation.idx_to_r(end_idx)
    return (
        ((side == Side.SENTE)
            and ((row_num == 1) or (row_num == 2))
        ) or (
        (side == Side.GOTE)
            and ((row_num == 9) or (row_num == 8))
        )
    )

def _drop(side: Side, ktype: KomaType, end_idx: int) -> Move:
    return Move(
        start_sq=Square.HAND,
        end_sq=BoardRepresentation.idx_to_sq(end_idx),
        koma=Koma.make(side, ktype)
    )

# === Promotion constrainers.
# They determine if there are promotion and/or nonpromotion moves
# given the piece type and the start and end squares.

def constrain_promotions_ky(
        side: Side, start_idx: int, end_idx: int
    ) -> List[Tuple[int, int, bool]]:
    res: List[Tuple[int, int, bool]] = []
    end_row_num = BoardRepresentation.idx_to_r(end_idx)
    must_promote = (
        (side == Side.SENTE and end_row_num == 1)
        or (side == Side.GOTE and end_row_num == 9)
    )
    can_promote = BoardRepresentation.is_idx_in_zone(end_idx, side)
    if must_promote:
        res.append((start_idx, end_idx, True))
    else:
        res.append((start_idx, end_idx, False))
        if can_promote:
            res.append((start_idx, end_idx, True))
    return res

def constrain_promotions_ke(
        side: Side, start_idx: int, end_idx: int
    ) -> List[Tuple[int, int, bool]]:
    res: List[Tuple[int, int, bool]] = []
    end_row_num = BoardRepresentation.idx_to_r(end_idx)
    must_promote = (
        (side == Side.SENTE and end_row_num in (1, 2))
        or (side == Side.GOTE and end_row_num in (8, 9))
    )
    can_promote = BoardRepresentation.is_idx_in_zone(end_idx, side)
    if must_promote:
        res.append((start_idx, end_idx, True))
    else:
        res.append((start_idx, end_idx, False))
        if can_promote:
            res.append((start_idx, end_idx, True))
    return res

def constrain_promotable(
        side: Side, start_idx: int, end_idx: int
    ) -> List[Tuple[int, int, bool]]:
    """Identify promotion and non-promotion moves for pieces that
    are not forced to promote and can move in and out of the
    promotion zone.
    """
    res: List[Tuple[int, int, bool]] = []
    can_promote = (
        BoardRepresentation.is_idx_in_zone(start_idx, side)
        or BoardRepresentation.is_idx_in_zone(end_idx, side)
    )
    res.append((start_idx, end_idx, False))
    if can_promote:
        res.append((start_idx, end_idx, True))
    return res

def constrain_unpromotable(
        side: Side, start_idx: int, end_idx: int
    ) -> List[Tuple[int, int, bool]]:
    """Identify promotion and non-promotion moves for pieces that
    cannot promote.
    """
    return [(start_idx, end_idx, False),]

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