from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsumemi.src.shogi.basetypes import Move
    from tsumemi.src.shogi.gametree import MoveNode

from tsumemi.src.shogi.gametree import GameNode
from tsumemi.src.shogi.position import Position


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
    
    def add_move(self, move: Move) -> None:
        self.curr_node = self.curr_node.add_move(move)
        self.position.make_move(move)
        return
    
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
    
    def to_notation(self):
        # Return human-readable notation format for mainline
        self.start()
        acc = []
        while not self.curr_node.is_leaf():
            self.next()
            acc.append(self.curr_node.move)
        return " ".join([mv.to_latin() for mv in acc])