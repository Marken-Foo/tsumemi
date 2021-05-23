from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import NullMove
from tsumemi.src.shogi.gametree import GameNode
from tsumemi.src.shogi.position import Position

if TYPE_CHECKING:
    from typing import List
    from tsumemi.src.shogi.basetypes import Move
    from tsumemi.src.shogi.gametree import MoveNode


class Game:
    def __init__(self) -> None:
        self.movetree = GameNode()
        self.curr_node: MoveNode = self.movetree
        self.position = Position()
        return
    
    def reset(self) -> None:
        self.movetree = GameNode()
        self.curr_node = self.movetree
        self.position.reset()
    
    def make_move(self, move: Move) -> None:
        self.curr_node = self.curr_node.add_move(move)
        self.position.make_move(move)
        return
    
    def is_move_mainline(self, move: Move) -> bool:
        return self.curr_node.next().move == move
    
    def next(self) -> None:
        self.position.make_move(self.curr_node.move)
        self.curr_node = self.curr_node.next()
        return
    
    def prev(self) -> None:
        self.position.unmake_move(self.curr_node.move)
        self.curr_node = self.curr_node.prev()
        return
    
    def start(self) -> None:
        self.position.from_sfen(self.movetree.start_pos)
        self.curr_node = self.movetree
        return
    
    def end(self) -> None:
        while not self.curr_node.is_leaf():
            self.next()
        return
    
    def to_notation(self) -> List[str]:
        # Return human-readable notation format for mainline
        self.start()
        res = []
        while not self.curr_node.is_leaf():
            self.next()
            res.append(self.curr_node.move.to_latin())
        return res
    
    def to_notation_ja_kif(self) -> List[str]:
        """Returns"""
        # Return human-readable KIF notation format for mainline
        self.start()
        res = []
        prev_move: Move = NullMove()
        while not self.curr_node.is_leaf():
            prev_move = self.curr_node.move
            self.next()
            mv: Move = self.curr_node.move
            if (not prev_move.is_null()) and (mv.end_sq == prev_move.end_sq):
                res.append(mv.to_ja_kif(is_same=True))
            else:
                res.append(mv.to_ja_kif())
        return res