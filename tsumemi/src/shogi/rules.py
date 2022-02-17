from __future__ import annotations

import functools

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, NullMove, Side, Square
from tsumemi.src.shogi.basetypes import HAND_TYPES, KOMA_TYPES
from tsumemi.src.shogi.position_internals import BoardRepresentation, Dir
from tsumemi.src.shogi.rules.destination_generation import *

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Tuple
    from tsumemi.src.shogi.position import Position


# === Public interface (functions meant to be used by other code)

def is_legal(mv: Move, pos: Position) -> bool:
    side = pos.turn
    pos.make_move(mv)
    ans = not is_in_check(pos, side)
    pos.unmake_move(mv)
    return ans

def generate_legal_moves(pos: Position) -> List[Move]:
    pass

def generate_valid_moves(
        pos: Position, side: Side, ktype: KomaType
    ) -> List[Move]:
    dest_generator, promotion_constrainer = MOVEGEN_FUNCTIONS[ktype]
    return generate_moves_base(
        pos=pos, side=side, ktype=ktype,
        dest_generator=dest_generator,
        promotion_constrainer=promotion_constrainer
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


# === Convenience functions to create Moves.

def _move(
        pos: Position, start_idx: int, end_idx: int, side: Side,
        ktype: KomaType, is_promotion=False
    ) -> Move:
    """Construct a Move given the relevant inputs. Convenient.
    """
    return Move(
        start_sq=BoardRepresentation.idx_to_sq(start_idx),
        end_sq=BoardRepresentation.idx_to_sq(end_idx),
        koma=Koma.make(side, ktype),
        captured=pos.board.mailbox[end_idx],
        is_promotion=is_promotion
    )

def _drop(side: Side, ktype: KomaType, end_idx: int) -> Move:
    """Construct a Move representing a drop, given the relevant
    inputs. Convenient.
    """
    return Move(
        start_sq=Square.HAND,
        end_sq=BoardRepresentation.idx_to_sq(end_idx),
        koma=Koma.make(side, ktype)
    )

# === For move generation

def generate_moves_base(
        pos: Position,
        side: Side,
        ktype: KomaType,
        dest_generator: Callable[[Position, int, Side], List[int]],
        promotion_constrainer: Callable[
            [Position, Side, int, int], List[Tuple[int, int, bool]]
        ]
    ) -> List[Move]:
    """Given a koma type (ktype), how it moves (dest_generator),
    and promotion constraints (promotion_constrainer), returns a
    list of all valid moves by that koma type (not counting drops)
    in the given Position (pos)."""
    mvlist = []
    locations = pos.board.koma_sets[Koma.make(side, ktype)]
    for start_idx in locations:
        destinations = dest_generator(pos, start_idx, side)
        # TODO: this requires internals of Position! Refactor!
        filtered_dests = [
            idx for idx in destinations if pos.board.mailbox[idx] != Koma.INVALID
        ]
        for end_idx in filtered_dests:
            tuplist = promotion_constrainer(pos, side, start_idx, end_idx)
            for tup in tuplist:
                start, end, promo = tup
                move = _move(pos, start, end, side, ktype, promo)
                mvlist.append(move)
    return mvlist

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

# === Basic reusable movement patterns of pieces

def _generate_line_idxs(
        pos: Position, side: Side, start_idx: int, dir: Dir
    ) -> List[int]:
    """Generate a list of target destination square indices,
    assuming a koma at location start_idx that moves in a line
    along the direction dir.
    """
    res = []
    dest = start_idx + dir
    dest_koma = pos.board.mailbox[dest]
    while dest_koma == Koma.NONE:
        res.append(dest)
        dest += dir
        dest_koma = pos.board.mailbox[dest]
    if dest_koma != Koma.INVALID and dest_koma.side() != side:
        res.append(dest)
    return res

def steps_fu(start_idx: int, side: Side) -> Tuple[int, ...]:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return (start_idx+forward,)

def steps_ke(start_idx: int, side: Side) -> Tuple[int, ...]:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return (
        start_idx+forward+forward+Dir.E,
        start_idx+forward+forward+Dir.W
    )

def steps_gi(start_idx: int, side: Side) -> Tuple[int, ...]:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return (
        start_idx+forward, start_idx+Dir.NE, start_idx+Dir.SE,
        start_idx+Dir.SW, start_idx+Dir.NW
    )

def steps_ki(start_idx: int, side: Side) -> Tuple[int, ...]:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return (
        start_idx+Dir.N, start_idx+Dir.S, start_idx+Dir.E, start_idx+Dir.W,
        start_idx+forward+Dir.E, start_idx+forward+Dir.W
    )

def steps_ou(start_idx: int, side: Side) -> Tuple[int, ...]:
    return (
        start_idx+Dir.N, start_idx+Dir.NE, start_idx+Dir.E,
        start_idx+Dir.SE, start_idx+Dir.S, start_idx+Dir.SW,
        start_idx+Dir.W, start_idx+Dir.NW
    )

# === Destination generators.
#  They may return invalid destinations.
#  Filter the output before use.

def generate_dests_steps(
        pos: Position, start_idx: int, side: Side,
        steps: Callable[[int, Side], Tuple[int, ...]]
    ) -> List[int]:
    res = []
    targets = steps(start_idx, side)
    for target in targets:
        target_koma = pos.board.mailbox[target]
        is_valid_target = (
            (target_koma != Koma.INVALID)
            and (target_koma == Koma.NONE or target_koma.side() != side)
        )
        if is_valid_target:
            res.append(target)
    return res

def generate_dests_ky(
        pos: Position, start_idx: int, side: Side
    ) -> List[int]:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return _generate_line_idxs(pos, side, start_idx, forward)

def generate_dests_ka(
        pos: Position, start_idx: int, side: Side
    ) -> List[int]:
    ne = _generate_line_idxs(pos, side, start_idx, Dir.NE)
    se = _generate_line_idxs(pos, side, start_idx, Dir.SE)
    nw = _generate_line_idxs(pos, side, start_idx, Dir.NW)
    sw = _generate_line_idxs(pos, side, start_idx, Dir.SW)
    return ne + se + nw + sw

def generate_dests_hi(
        pos: Position, start_idx: int, side: Side
    ) -> List[int]:
    n = _generate_line_idxs(pos, side, start_idx, Dir.N)
    s = _generate_line_idxs(pos, side, start_idx, Dir.S)
    e = _generate_line_idxs(pos, side, start_idx, Dir.E)
    w = _generate_line_idxs(pos, side, start_idx, Dir.W)
    return n + s + e + w

def generate_dests_um(
        pos: Position, start_idx: int, side: Side
    ) -> List[int]:
    kaku = generate_dests_ka(pos, start_idx, side)
    wazir = [
        start_idx+Dir.N, start_idx+Dir.S,
        start_idx+Dir.E, start_idx+Dir.W
    ]
    return kaku + wazir

def generate_dests_ry(
        pos: Position, start_idx: int, side: Side
    ) -> List[int]:
    hisha = generate_dests_hi(pos, start_idx, side)
    alfil = [
        start_idx+Dir.NE, start_idx+Dir.SE,
        start_idx+Dir.SW, start_idx+Dir.NW
    ]
    return hisha + alfil

# === Promotion constrainers.
# They determine if there are promotion and/or nonpromotion moves
# given the piece type and the start and end squares.

def constrain_promotions_ky(
        pos: Position, side: Side, start_idx: int, end_idx: int
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
        pos: Position, side: Side, start_idx: int, end_idx: int
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
        pos: Position, side: Side, start_idx: int, end_idx: int
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
        pos: Position, side: Side, start_idx: int, end_idx: int
    ) -> List[Tuple[int, int, bool]]:
    """Identify promotion and non-promotion moves for pieces that
    cannot promote.
    """
    return [(start_idx, end_idx, False),]

# Contains the functions to generate valid moves for each KomaType.
MOVEGEN_FUNCTIONS: Dict[KomaType,
        Tuple[Callable[..., Any], Callable[..., Any]]
    ] = {
    KomaType.FU: (
        functools.partial(generate_dests_steps, steps=steps_fu),
        constrain_promotions_ky
    ),
    KomaType.KY: (generate_dests_ky, constrain_promotions_ky),
    KomaType.KE: (
        functools.partial(generate_dests_steps, steps=steps_ke),
        constrain_promotions_ke
    ),
    KomaType.GI: (
        functools.partial(generate_dests_steps, steps=steps_gi),
        constrain_promotable
    ),
    KomaType.KI: (
        functools.partial(generate_dests_steps, steps=steps_ki),
        constrain_unpromotable
    ),
    KomaType.KA: (generate_dests_ka, constrain_promotable),
    KomaType.HI: (generate_dests_hi, constrain_promotable),
    KomaType.OU: (
        functools.partial(generate_dests_steps, steps=steps_ou),
        constrain_unpromotable
    ),
    KomaType.TO: (
        functools.partial(generate_dests_steps, steps=steps_ki),
        constrain_unpromotable
    ),
    KomaType.NY: (
        functools.partial(generate_dests_steps, steps=steps_ki),
        constrain_unpromotable
    ),
    KomaType.NK: (
        functools.partial(generate_dests_steps, steps=steps_ki),
        constrain_unpromotable
    ),
    KomaType.NG: (
        functools.partial(generate_dests_steps, steps=steps_ki),
        constrain_unpromotable
    ),
    KomaType.UM: (generate_dests_um, constrain_unpromotable),
    KomaType.RY: (generate_dests_ry, constrain_unpromotable),
}