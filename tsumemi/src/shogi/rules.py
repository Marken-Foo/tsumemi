from __future__ import annotations

from typing import List

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Side, Square
from tsumemi.src.shogi.position import Dir, Position


class Rules:
    def is_legal(self, mv: Move, pos: Position) -> bool:
        side = pos.turn
        pos.make_move(mv)
        ans = self.is_suicide(side, pos)
        pos.unmake_move(mv)
        return ans
    
    def generate_legal_moves(self, pos: Position) -> List[Move]:
        pass
    
    def generate_pawn_moves(self, side: Side, pos: Position) -> List[Move]:
        mvlist = []
        locations = pos.koma_sets[Koma.make(side, KomaType.FU)]
        forward = Dir.S if side == Side.GOTE else Dir.N
        for start_idx in locations:
            end_idx = start_idx + forward
            if pos.board[end_idx] == Koma.INVALID:
                continue
            move = Move(
                start_sq=pos.idx_to_sq(start_idx),
                end_sq=pos.idx_to_sq(end_idx),
                koma=Koma.make(side, KomaType.FU)
            )
            mvlist.append(move)
            # Make promotion moves
            if pos.is_idx_in_zone(side=side, idx=end_idx) or pos.is_idx_in_zone(side=side, idx=start_idx):
                move = Move(
                    start_sq=pos.idx_to_sq(start_idx),
                    end_sq=pos.idx_to_sq(end_idx),
                    is_promotion=True,
                    koma=Koma.make(side, KomaType.FU)
                )
                mvlist.append(move)
        return mvlist
    
    def generate_drop_moves(self, side: Side, pos: Position) -> List[Move]:
        pass
    
    def is_suicide(self, side: Side, pos: Position) -> bool:
        pass