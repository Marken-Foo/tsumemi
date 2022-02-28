from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import NullMove
from tsumemi.src.shogi.gametree import GameNode
from tsumemi.src.shogi.position import Position

if TYPE_CHECKING:
    from typing import List
    from tsumemi.src.shogi.basetypes import Move
    from tsumemi.src.shogi.gametree import MoveNode
    from tsumemi.src.shogi.notation_writer import AbstractMoveWriter


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
        self.position.make_move(move) # should check for exceptions
        self.curr_node = self.curr_node.add_move(move)
        return
    
    def make_move(self, move: Move) -> bool:
        """If the move exists in the movetree, execute the move. If
        not, don't do anything.
        """
        res = self.curr_node.has_as_next_move(move)
        if res:
            self.position.make_move(move) # should check for exceptions
            self.curr_node = self.curr_node.get_variation_node(move)
        return res
    
    def is_mainline(self, move: Move) -> bool:
        if self.curr_node.is_leaf():
            return False
        else:
            return self.curr_node.next().move == move
    
    def is_end(self) -> bool:
        return self.curr_node.is_leaf()
    
    def get_mainline_move(self) -> Move:
        next_node = self.curr_node.next()
        return next_node.move
    
    def go_next_move(self) -> bool:
        """Go one move further into the game, following the mainline.
        """
        next_node = self.curr_node.next()
        if next_node.is_null():
            return False
        self.position.make_move(next_node.move)
        self.curr_node = next_node
        return True
    
    def go_prev_move(self) -> None:
        """Step one move back in the game.
        """
        prev_node = self.curr_node.prev()
        if prev_node.is_null():
            return
        self.position.unmake_move(self.curr_node.move)
        self.curr_node = prev_node
        return
    
    def go_to_start(self) -> None:
        """Go to the start of the game.
        """
        self.position.from_sfen(self.movetree.start_pos)
        self.curr_node = self.movetree
        return
    
    def go_to_end(self) -> None:
        """Go to the end of the current branch.
        """
        has_next = True
        while has_next:
            has_next = self.go_next_move()
        return
    
    def get_current_sfen(self) -> str:
        return self.position.to_sfen()
    
    def get_mainline_notation(self,
            move_writer: AbstractMoveWriter
        ) -> List[str]:
        # Make a new Game to leave self unchanged
        game = Game()
        game.movetree = self.movetree
        game.curr_node = self.movetree
        game.go_to_start()
        res = []
        while not game.curr_node.is_leaf():
            prev_move = game.curr_node.move
            game.go_next_move()
            move: Move = game.curr_node.move
            is_same_dest = (
                (not prev_move.is_null())
                and (move.end_sq == prev_move.end_sq)
            )
            res.append(move_writer.write_move(
                move, game.position, is_same_dest
            ))
        return res
