from __future__ import annotations

import functools

from typing import Callable, List, Tuple

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Side, Square, HAND_TYPES
from tsumemi.src.shogi.position import Dir, Position


def is_legal(mv: Move, pos: Position) -> bool:
    side = pos.turn
    pos.make_move(mv)
    ans = is_suicide(pos, side)
    pos.unmake_move(mv)
    return ans

def generate_legal_moves(pos: Position) -> List[Move]:
    pass

def _generate_line_idxs(
        pos: Position, side: Side, start_idx: int, dir: Dir
    ) -> List[int]:
    """Generate a list of target destination square indices,
    assuming a koma at location start_idx that moves in a line
    along the direction dir.
    """
    res = []
    dest = start_idx + dir
    dest_koma = pos.board[dest]
    while dest_koma == Koma.NONE:
        res.append(dest)
        dest += dir
        dest_koma = pos.board[dest]
    if dest_koma != Koma.INVALID and dest_koma.side() != side:
        res.append(dest)
    return res

def _move(
        pos: Position, start_idx: int, end_idx: int, side: Side,
        ktype: KomaType, is_promotion=False
    ) -> Move:
    """Construct a Move given the relevant inputs. Convenient.
    """
    return Move(
        start_sq=pos.idx_to_sq(start_idx), end_sq=pos.idx_to_sq(end_idx),
        koma=Koma.make(side, ktype), captured=pos.board[end_idx],
        is_promotion=is_promotion
    )

def _drop(
        pos: Position, end_idx: int, side: Side, ktype: KomaType
    ) -> Move:
    """Construct a Move representing a drop, given the relevant
    inputs. Convenient.
    """
    return Move(
        start_sq=Square.HAND, end_sq=pos.idx_to_sq(end_idx),
        koma=Koma.make(side, ktype)
    )

def generate_moves_base(
        pos: Position, side: Side, ktype: KomaType,
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
    locations = pos.koma_sets[Koma.make(side, ktype)]
    for start_idx in locations:
        destinations = dest_generator(pos, start_idx, side)
        for end_idx in destinations:
            tuplist = promotion_constrainer(pos, side, start_idx, end_idx)
            for tup in tuplist:
                start, end, promo = tup
                move = _move(pos, start, end, side, ktype, promo)
                mvlist.append(move)
    return mvlist

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

def generate_dests_steps(
        pos: Position, start_idx: int, side: Side,
        steps: Callable[[int, Side], Tuple[int, ...]]
    ) -> List[int]:
    res = []
    targets = steps(start_idx, side)
    for target in targets:
        target_koma = pos.board[target]
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

def constrain_promotions_ky(
        pos: Position, side: Side, start_idx: int, end_idx: int
    ) -> List[Tuple[int, int, bool]]:
    res: List[Tuple[int, int, bool]] = []
    must_promote = (
        (side == Side.SENTE and pos.idx_to_r(end_idx) == 1)
        or (side == Side.GOTE and pos.idx_to_r(end_idx) == 9)
    )
    can_promote = pos.is_idx_in_zone(end_idx, side)
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
    must_promote = (
        (side == Side.SENTE and pos.idx_to_r(end_idx) in (1, 2))
        or (side == Side.GOTE and pos.idx_to_r(end_idx) in (8, 9))
    )
    can_promote = pos.is_idx_in_zone(end_idx, side)
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
    can_promote = pos.is_idx_in_zone(start_idx, side) or pos.is_idx_in_zone(end_idx, side)
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

def generate_valid_moves(pos: Position, side: Side, ktype: KomaType) -> List[Move]:
    dest_generator, promotion_constrainer = MOVEGEN_FUNCTIONS[ktype]
    return generate_moves_base(
        pos=pos, side=side, ktype=ktype,
        dest_generator=dest_generator,
        promotion_constrainer=promotion_constrainer
    )

def generate_drop_moves(pos: Position, side: Side, ktype: KomaType) -> List[Move]:
    if ktype not in HAND_TYPES:
        return []
    mvlist: List[Move] = []
    hand = pos.hand_sente if side == Side.SENTE else pos.hand_gote
    if hand[ktype] == 0:
        return mvlist
    for end_idx in pos.empty_idxs:
        if ktype == KomaType.FU:
            row_num = pos.idx_to_r(end_idx)
            if ((side == Side.SENTE) and (row_num == 1)) or ((side == Side.GOTE) and (row_num == 9)):
                continue
            # nifu
            col = pos.idx_to_c(end_idx)
            is_nifu = False
            for row in range(1, 10, 1):
                idx = pos.cr_to_idx(col, row)
                if pos.board[idx] == Koma.make(side, KomaType.FU):
                    is_nifu = True
            if is_nifu:
                continue
        elif ktype == KomaType.KY:
            row_num = pos.idx_to_r(end_idx)
            if ((side == Side.SENTE) and (row_num == 1)) or ((side == Side.GOTE) and (row_num == 9)):
                continue
        elif ktype == KomaType.KE:
            row_num = pos.idx_to_r(end_idx)
            if ((side == Side.SENTE) and ((row_num == 1) or (row_num == 2))) or ((side == Side.GOTE) and ((row_num == 9) or (row_num == 8))):
                continue
        move = _drop(
            pos=pos, end_idx=end_idx, side=side, ktype=ktype
        )
        mvlist.append(move)
    return mvlist

def is_suicide(pos: Position, side: Side) -> bool:
    pass


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