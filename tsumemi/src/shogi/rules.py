from __future__ import annotations

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
    
    def _generate_line_idxs(self, side: Side, pos: Position, start_idx: int, dir: Dir) -> List[int]:
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
    
    def generate_moves(self, pos: Position, side: Side, ktype: KomaType, target_generator, promotion_generator) -> List[Move]:
        mvlist = []
        locations = pos.koma_sets[Koma.make(side, ktype)]
        for start_idx in locations:
            targets = target_generator(pos, start_idx, side)
            for end_idx in targets:
                tuplist = promotion_generator(pos, side, start_idx, end_idx)
                for tup in tuplist:
                    start, end, promo = tup
                    move = self._move(pos, start, end, side, ktype, promo)
                    mvlist.append(move)
        return mvlist
    
    def generate_targets_fu(self, pos: Position, start_idx: int, side: Side) -> List[int]:
        targets = []
        forward = Dir.S if side == Side.GOTE else Dir.N
        end_idx = start_idx + forward
        target_koma = pos.board[end_idx]
        is_valid_target = ((target_koma != Koma.INVALID)
            and (target_koma == Koma.NONE or target_koma.side != side)
        )
        if is_valid_target:
            targets.append(end_idx)
        return targets
    
    def generate_promotions_fu(self, pos: Position, side: Side, start_idx: int, end_idx: int) -> List[Tuple[int, int, bool]]:
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
    
    def generate_moves_fu(self, pos: Position, side: Side) -> List[Move]:
        return self.generate_moves(pos, side, KomaType.FU, self.generate_targets_fu, self.generate_promotions_fu)
    
    def generate_moves_ky(self, side: Side, pos: Position) -> List[Move]:
        mvlist = []
        ktype = KomaType.KY
        forward = Dir.S if side == Side.GOTE else Dir.N
        locations = pos.koma_sets[Koma.make(side, ktype)]
        for start_idx in locations:
            targets = self._generate_line_idxs(side, pos, start_idx, forward)
            for end_idx in targets:
                move = self._move(pos, start_idx, end_idx, side, ktype)
                mvlist.append(move)
                # Make promotion moves
                can_promote = (pos.is_idx_in_zone(side=side, idx=end_idx)
                    or pos.is_idx_in_zone(side=side, idx=start_idx)
                )
                if can_promote:
                    move = self._move(pos, start_idx, end_idx, side, ktype, is_promotion=True)
                    mvlist.append(move)
        return mvlist
    
    def generate_moves_ke(self, side: Side, pos: Position) -> List[Move]:
        mvlist = []
        ktype = KomaType.KE
        forward = Dir.S if side == Side.GOTE else Dir.N
        locations = pos.koma_sets[Koma.make(side, ktype)]
        for start_idx in locations:
            targets = (start_idx+forward+forward+Dir.E, start_idx+forward+forward+Dir.W)
            for end_idx in targets:
                move = self._move(pos, start_idx, end_idx, side, ktype)
                mvlist.append(move)
                # Make promotion moves
                can_promote = (pos.is_idx_in_zone(side=side, idx=end_idx)
                    or pos.is_idx_in_zone(side=side, idx=start_idx)
                )
                if can_promote:
                    move = self._move(pos, start_idx, end_idx, side, ktype, is_promotion=True)
                    mvlist.append(move)
        return mvlist
    
    def generate_drop_moves(self, side: Side, pos: Position) -> List[Move]:
        pass
    
    def is_suicide(self, side: Side, pos: Position) -> bool:
        pass