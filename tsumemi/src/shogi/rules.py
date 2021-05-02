from __future__ import annotations

import functools

from typing import List, Tuple

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Side, Square
from tsumemi.src.shogi.position import Dir, Position


class Rules:
    def __init__(self) -> None:
        return
    
    def is_legal(self, mv: Move, pos: Position) -> bool:
        side = pos.turn
        pos.make_move(mv)
        ans = self.is_suicide(side, pos)
        pos.unmake_move(mv)
        return ans
    
    def generate_legal_moves(self, pos: Position) -> List[Move]:
        pass
    
    def _generate_line_idxs(self, pos: Position, side: Side, start_idx: int, dir: Dir) -> List[int]:
        targets = []
        target = start_idx + dir
        target_koma = pos.board[target]
        while target_koma == Koma.NONE:
            targets.append(target)
            target += dir
            target_koma = pos.board[target]
        if target_koma != Koma.INVALID and target_koma.side != side:
            targets.append(target)
        return targets
    
    def _move(self, pos: Position, start_idx: int, end_idx: int, side: Side, ktype: KomaType, is_promotion=False) -> Move:
        return Move(
            start_sq=pos.idx_to_sq(start_idx), end_sq=pos.idx_to_sq(end_idx),
            koma=Koma.make(side, ktype), captured=pos.board[end_idx],
            is_promotion=is_promotion
        )
    
    def generate_moves(self, pos: Position, side: Side, ktype: KomaType, dest_generator, promotion_constrainer) -> List[Move]:
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
                    move = self._move(pos, start, end, side, ktype, promo)
                    mvlist.append(move)
        return mvlist
    
    def steps_fu(self, start_idx: int, side: Side) -> Tuple[int, ...]:
        forward = Dir.S if side == Side.GOTE else Dir.N
        return (start_idx+forward,)
    
    def steps_ke(self, start_idx: int, side: Side) -> Tuple[int, ...]:
        forward = Dir.S if side == Side.GOTE else Dir.N
        return (
            start_idx+forward+forward+Dir.E,
            start_idx+forward+forward+Dir.W
        )
    
    def steps_gi(self, start_idx: int, side: Side) -> Tuple[int, ...]:
        forward = Dir.S if side == Side.GOTE else Dir.N
        return (
            start_idx+forward, start_idx+Dir.NE, start_idx+Dir.SE,
            start_idx+Dir.SW, start_idx+Dir.NW
        )
    
    def steps_ki(self, start_idx: int, side: Side) -> Tuple[int, ...]:
        forward = Dir.S if side == Side.GOTE else Dir.N
        return (
            start_idx+Dir.N, start_idx+Dir.S, start_idx+Dir.E, start_idx+Dir.W,
            start_idx+forward+Dir.E, start_idx+forward+Dir.W
        )
    
    def steps_ou(self, start_idx: int, side: Side) -> Tuple[int, ...]:
        return (
            start_idx+Dir.N, start_idx+Dir.NE, start_idx+Dir.E,
            start_idx+Dir.SE, start_idx+Dir.S, start_idx+Dir.SW,
            start_idx+Dir.W, start_idx+Dir.NW
        )
    
    def generate_dests_steps(self, pos: Position, start_idx: int, side: Side, steps) -> List[int]:
        res = []
        targets = steps(start_idx, side)
        for target in targets:
            target_koma = pos.board[target]
            is_valid_target = ((target_koma != Koma.INVALID)
                and (target_koma == Koma.NONE or target_koma.side != side)
            )
            if is_valid_target:
                res.append(target)
        return res
    
    def generate_dests_ky(self, pos: Position, start_idx: int, side: Side) -> List[int]:
        forward = Dir.S if side == Side.GOTE else Dir.N
        return self._generate_line_idxs(pos, side, start_idx, forward)
    
    def generate_dests_ka(self, pos: Position, start_idx: int, side: Side) -> List[int]:
        ne = self._generate_line_idxs(pos, side, start_idx, Dir.NE)
        se = self._generate_line_idxs(pos, side, start_idx, Dir.SE)
        nw = self._generate_line_idxs(pos, side, start_idx, Dir.NW)
        sw = self._generate_line_idxs(pos, side, start_idx, Dir.SW)
        return ne + se + nw + sw
    
    def generate_dests_hi(self, pos: Position, start_idx: int, side: Side) -> List[int]:
        n = self._generate_line_idxs(pos, side, start_idx, Dir.N)
        s = self._generate_line_idxs(pos, side, start_idx, Dir.S)
        e = self._generate_line_idxs(pos, side, start_idx, Dir.E)
        w = self._generate_line_idxs(pos, side, start_idx, Dir.W)
        return n + s + e + w
    
    def generate_dests_um(self, pos: Position, start_idx: int, side: Side) -> List[int]:
        kaku = self.generate_dests_ka(pos, start_idx, side)
        wazir = [
            start_idx+Dir.N, start_idx+Dir.S,
            start_idx+Dir.E, start_idx+Dir.W
        ]
        return kaku + wazir
    
    def generate_dests_ry(self, pos: Position, start_idx: int, side: Side) -> List[int]:
        hisha = self.generate_dests_hi(pos, start_idx, side)
        alfil = [
            start_idx+Dir.NE, start_idx+Dir.SE,
            start_idx+Dir.SW, start_idx+Dir.NW
        ]
        return hisha + alfil
    
    def constrain_promotions_ky(self, pos: Position, side: Side, start_idx: int, end_idx: int) -> List[Tuple[int, int, bool]]:
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
    
    def constrain_promotions_ke(self, pos: Position, side: Side, start_idx: int, end_idx: int) -> List[Tuple[int, int, bool]]:
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
    
    def constrain_promotable(self, pos: Position, side: Side, start_idx: int, end_idx: int) -> List[Tuple[int, int, bool]]:
        """Identify promotion and non-promotion moves for pieces that
        are not forced to promote and can move in and out of the
        promotion zone.
        """
        res: List[Tuple[int, int, bool]] = []
        must_promote = False
        can_promote = pos.is_idx_in_zone(start_idx, side) or pos.is_idx_in_zone(end_idx, side)
        if must_promote:
            res.append((start_idx, end_idx, True))
        else:
            res.append((start_idx, end_idx, False))
            if can_promote:
                res.append((start_idx, end_idx, True))
        return res
    
    def constrain_unpromotable(self, pos: Position, side: Side, start_idx: int, end_idx: int) -> List[Tuple[int, int, bool]]:
        """Identify promotion and non-promotion moves for pieces that
        cannot promote.
        """
        res: List[Tuple[int, int, bool]] = []
        must_promote = False
        can_promote = False
        if must_promote:
            res.append((start_idx, end_idx, True))
        else:
            res.append((start_idx, end_idx, False))
            if can_promote:
                res.append((start_idx, end_idx, True))
        return res
    
    def generate_moves_fu(self, pos: Position, side: Side) -> List[Move]:
        # FU and KY use the same promotion constraints
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_fu)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.FU,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_promotions_ky
        )
    
    def generate_moves_ky(self, side: Side, pos: Position) -> List[Move]:
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.KY,
            dest_generator=self.generate_dests_ky,
            promotion_constrainer=self.constrain_promotions_ky
        )
    
    def generate_moves_ke(self, side: Side, pos: Position) -> List[Move]:
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_ke)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.KE,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_promotions_ke
        )
    
    def generate_moves_gi(self, side: Side, pos: Position) -> List[Move]:
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_gi)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.GI,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_promotable
        )
    
    def generate_moves_ki(self, side: Side, pos: Position) -> List[Move]:
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_ki)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.KI,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_promotable
        )
    
    def generate_moves_ka(self, side: Side, pos: Position) -> List[Move]:
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.KA,
            dest_generator=self.generate_dests_ka,
            promotion_constrainer=self.constrain_promotable
        )
    
    def generate_moves_hi(self, side: Side, pos: Position) -> List[Move]:
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.HI,
            dest_generator=self.generate_dests_hi,
            promotion_constrainer=self.constrain_promotable
        )
    
    def generate_moves_ou(self, side: Side, pos: Position) -> List[Move]:
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_ou)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.OU,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_unpromotable
        )
    
    def generate_moves_to(self, side: Side, pos: Position) -> List[Move]:
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_ki)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.TO,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_unpromotable
        )
    
    def generate_moves_ny(self, side: Side, pos: Position) -> List[Move]:
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_ki)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.NY,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_unpromotable
        )
    
    def generate_moves_nk(self, side: Side, pos: Position) -> List[Move]:
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_ki)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.NK,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_unpromotable
        )
    
    def generate_moves_ng(self, side: Side, pos: Position) -> List[Move]:
        step_gen = functools.partial(self.generate_dests_steps, steps=self.steps_ki)
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.NG,
            dest_generator=step_gen,
            promotion_constrainer=self.constrain_unpromotable
        )
    
    def generate_moves_um(self, side: Side, pos: Position) -> List[Move]:
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.UM,
            dest_generator=self.generate_dests_um,
            promotion_constrainer=self.constrain_unpromotable
        )
    
    def generate_moves_ry(self, side: Side, pos: Position) -> List[Move]:
        return self.generate_moves(
            pos=pos, side=side, ktype=KomaType.RY,
            dest_generator=self.generate_dests_ry,
            promotion_constrainer=self.constrain_unpromotable
        )
    
    def generate_drop_moves(self, side: Side, pos: Position) -> List[Move]:
        pass
    
    def is_suicide(self, side: Side, pos: Position) -> bool:
        pass