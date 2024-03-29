from __future__ import annotations

from typing import NewType, TYPE_CHECKING

from tsumemi.src.shogi.move import NullMove

if TYPE_CHECKING:
    from typing import Any, Callable, Generator, Iterator, List
    from tsumemi.src.shogi.move import Move
    from tsumemi.src.shogi.notation import AbstractMoveWriter
    from tsumemi.src.shogi.position import Position


MoveNodeId = NewType("MoveNodeId", int)


class MoveNode:
    """A node in a movetree. Each node contains the move leading to
    it, and the comment attached to the move, if any.
    Each node also contains a reference to its parent, and an ordered
    list of child nodes (the mainline is first in the list).
    """
    _id = 0 # running unique ID for MoveNodes

    def __init__(self, move: Move, parent: MoveNode) -> None:
        self.move: Move = move # move leading to this node
        self.parent: MoveNode = parent
        self.movenum: int = 0 if parent.is_null() else parent.movenum + 1
        self.comment: str = ""
        self.variations: List[MoveNode] = []
        # implementation detail
        self.id: MoveNodeId = MoveNodeId(MoveNode._id)
        MoveNode._id += 1
        return

    def is_null(self) -> bool:
        return False

    def is_leaf(self) -> bool:
        return not bool(self.variations)

    def has_variations(self) -> bool:
        return len(self.variations) > 1

    def add_move(self, move: Move) -> MoveNode:
        """Add a new node to the movetree. If move already exists as a
        variation, don't create a new node but return the existing
        variation node.
        """
        for node in self.variations:
            if move == node.move:
                return node
        new_node = MoveNode(move, self)
        self.variations.append(new_node)
        return new_node

    def has_as_next_move(self, move: Move) -> bool:
        return any(node.move == move for node in self.variations)

    def get_variation_node(self, move: Move) -> MoveNode:
        """Return the child node corresponding to the given move.
        """
        for node in self.variations:
            if move == node.move:
                return node
        raise ValueError(
            f"Move ({str(move)}) is not a variation after move (str(self.movenum))"
        )

    def get_path_from_root(self) -> Iterator[MoveNode]:
        """Returns an iterator of MoveNodes leading from the root of
        the gametree to the caller node, inclusive.
        """
        node = self
        res = []
        while not node.is_null():
            res.append(node)
            node = node.parent
        return reversed(res)

    def get_last_node(self) -> MoveNode:
        """Returns the node at the end of the mainline from this node.
        """
        node = self
        while node.variations:
            node = node.variations[0]
        return node

    def next(self) -> MoveNode:
        return self.variations[0] if self.variations else NullMoveNode()

    def prev(self) -> MoveNode:
        return self.parent

    def traverse_preorder(self) -> Generator[MoveNode, None, None]:
        """Traverse the game tree from this node by preorder.
        This will yield the mainline first. Includes the called node.
        """
        yield self
        for node in self.variations:
            yield from node.traverse_preorder()

    def traverse_mainline(self) -> Generator[MoveNode, None, None]:
        """Traverse only the mainline of this node. Includes the
        called node.
        """
        yield self
        if self.variations:
            yield from self.variations[0].traverse_mainline()

    def write_move(self,
            move_writer: AbstractMoveWriter,
            position: Position,
        ) -> str:
        """Returns the node's move as a string in the format of
        `move_writer`. The `position` is required for disambiguation.
        """
        if self.move.is_null():
            return ""
        is_same_sq = (
            not self.parent.move.is_null()
            and self.parent.move.end_sq == self.move.end_sq
        )
        return move_writer.write_move(self.move, position, is_same_sq)

    def _rec_str(self, acc: List[Any],
            func: Callable[[MoveNode, List[Any]], None]
            ) -> None:
        """Recursive method to allow GameNode to print game tree.
        """
        func(self, acc)
        if not self.variations:
            return
        for node in self.variations:
            node._rec_str(acc, func)

    def _str_move(self, acc: List[str]) -> None:
        if not self.move.is_null():
            acc.append(str(self.movenum) + "." + str(self.move))
        return

    def _latin_move(self, acc: List[str]) -> None:
        if not self.move.is_null():
            acc.append(str(self.movenum) + "." + self.move.to_latin())
        return


class NullMoveNode(MoveNode):
    """Null object to act as sentinel.
    """
    def __init__(self) -> None:
        super().__init__(move=NullMove(), parent=self)
        return

    def is_null(self) -> bool:
        return True


class GameNode(MoveNode):
    """The root node of a movetree. Contains extra information like
    the starting position (handicap/nonstandard game, or a problem
    position) and the player names.
    """
    def __init__(self) -> None:
        super().__init__(NullMove(), NullMoveNode())
        self.sente: str = ""
        self.gote: str = ""
        self.handicap: str = ""
        self.start_pos: str = "" # sfen
        return

    def __str__(self) -> str:
        acc: List[str] = []
        self._rec_str(acc, MoveNode._str_move)
        return " ".join(acc)

    def to_latin(self) -> str:
        acc: List[str] = []
        self._rec_str(acc, MoveNode._latin_move)
        return " ".join(acc)
