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
    """Representation of a shogi game. Contains a reference to the
    root of the movetree, the current active node, and the current
    position in the game.
    """
    def __init__(self) -> None:
        self.movetree = GameNode()
        self.curr_node: MoveNode = self.movetree
        self.position = Position()
        return
    
    def reset(self) -> None:
        """Reset self to a new empty game.
        """
        self.movetree = GameNode()
        self.curr_node = self.movetree
        self.position.reset()
    
    def add_move(self, move: Move) -> None:
        """Execute the given move and add it to the movetree if it
        doesn't already exist.
        """
        self.curr_node = self.curr_node.add_move(move)
        self.position.make_move(move)
        return
    
    def make_move(self, move: Move) -> bool:
        """If the move exists in the movetree, execute the move. If
        not, don't do anything.
        """
        res = self.curr_node.has_move(move)
        if res:
            self.curr_node = self.curr_node.get_variation_node(move)
            self.position.make_move(move)
        return res
    
    def is_mainline(self, move: Move) -> bool:
        if self.curr_node.is_leaf():
            return False
        else:
            return self.curr_node.next().move == move
    
    def is_start(self) -> bool:
        return self.curr_node.parent.is_null()
    
    def is_end(self) -> bool:
        return self.curr_node.is_leaf()
    
    def get_mainline_move(self) -> Move:
        next_node = self.curr_node.next()
        if self.curr_node == next_node:
            return NullMove()
        else:
            return next_node.move
    
    def next(self) -> bool:
        """Go one move further into the game, following the mainline.
        """
        if self.curr_node.is_leaf():
            return False
        else:
            next_node = self.curr_node.next()
            self.position.make_move(next_node.move)
            self.curr_node = next_node
            return True
    
    def prev(self) -> None:
        """Step one move back in the game.
        """
        if self.curr_node.prev() == self.curr_node:
            return
        else:
            self.position.unmake_move(self.curr_node.move)
            self.curr_node = self.curr_node.prev()
            return
    
    def start(self) -> None:
        """Go to the start of the game.
        """
        self.position.from_sfen(self.movetree.start_pos)
        self.curr_node = self.movetree
        return
    
    def end(self) -> None:
        """Go to the end of the current branch.
        """
        has_next = True
        while has_next:
            has_next = self.next()
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