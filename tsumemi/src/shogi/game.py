from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.gametree import GameNode
from tsumemi.src.shogi.position import Position

if TYPE_CHECKING:
    from typing import Generator, Iterable, List, Optional
    from tsumemi.src.shogi.gametree import MoveNode
    from tsumemi.src.shogi.move import Move
    from tsumemi.src.shogi.notation import AbstractMoveWriter


class Game:
    """Representation of a shogi game. Contains a reference to the
    root of the movetree, the current active node, and the current
    position in the game.
    """
    def __init__(self) -> None:
        self.movetree: GameNode = GameNode()
        self.curr_node: MoveNode = self.movetree
        self.position: Position = Position()
        return

    def copy_from(self, game: Game) -> None:
        """Shallow copy provided game onto self.
        """
        self.movetree = game.movetree
        self.curr_node = game.curr_node
        self.position = game.position
        return

    def reset(self) -> None:
        """Reset self to a new empty game.
        """
        self.movetree = GameNode()
        self.curr_node = self.movetree
        self.position.reset()
        return

    def get_last_move(self) -> Move:
        """Returns the move leading to the current game state.
        """
        return self.curr_node.move

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
        return self.curr_node.next().move == move

    def is_end(self) -> bool:
        return self.curr_node.is_leaf()

    def has_variations(self) -> bool:
        return self.curr_node.has_variations()

    def get_mainline_move(self) -> Move:
        next_node = self.curr_node.next()
        return next_node.move

    def go_next_move(self) -> None:
        """Go one move further into the game, following the mainline.
        """
        next_node = self.curr_node.next()
        if next_node.is_null():
            return
        self.position.make_move(next_node.move)
        self.curr_node = next_node
        return

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
        if not self.movetree.start_pos:
            # This should not happen, but needs to be handled
            return
        self.position.from_sfen(self.movetree.start_pos)
        self.curr_node = self.movetree
        return

    def go_to_end(self) -> None:
        """Go to the end of the current branch.
        """
        while not self.is_end():
            self.go_next_move()
        return

    def go_to_id(self, _id: int) -> None:
        """Go to the node with the given id.
        """
        for node in self.movetree.traverse_preorder():
            if node.id == _id:
                target_node = node
                break
        else:
            # Node not found, do nothing
            return
        self._go_to_node(target_node)
        return

    def _go_to_node(self, target_node: MoveNode) -> None:
        """Go to the target node, assuming it is in the movetree.
        """
        path_nodes = target_node.get_path_from_root()
        path_nodes.__next__() # exclude the root node
        self.position = self.get_end_position(
            (node.move for node in path_nodes)
        )
        self.curr_node = target_node
        return

    def get_current_sfen(self) -> str:
        return self.position.to_sfen()

    def get_movelist(self) -> Generator[Optional[Move], None, None]:
        return (
            None if node.is_null() else node.move
            for node in self.movetree.traverse_preorder()
        )

    def get_end_position(self, moves: Iterable[Move]) -> Position:
        position = Position()
        position.from_sfen(self.movetree.start_pos)
        for move in moves:
            position.make_move(move)
        return position

    def get_mainline_notation(self,
            move_writer: AbstractMoveWriter
        ) -> List[str]:
        pos = Position()
        pos.from_sfen(self.movetree.start_pos)
        res = []
        nodes = self.movetree.traverse_mainline()
        nodes.__next__() # exclude the root node
        for node in nodes:
            pos.make_move(node.move)
            res.append(node.write_move(move_writer, pos))
        return res
