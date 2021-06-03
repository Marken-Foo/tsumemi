from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import NullMove

if TYPE_CHECKING:
    from typing import Any, Callable, List, Optional
    from tsumemi.src.shogi.basetypes import Move


class MoveNode:
    """A node in a movetree. Each node contains the move leading to
    it, and the comment attached to the move, if any.
    As part of the tree structure, the MoveNode contains a reference
    to its parent, and a list of child nodes in order of importance
    (the mainline is the first in the list).
    """
    def __init__(self, move: Move = NullMove(),
            parent: Optional[MoveNode] = None
        ) -> None:
        self.move = move # move leading to this node
        self.parent: MoveNode = NullMoveNode() if parent is None else parent
        self.movenum: int = 0 if parent is None else parent.movenum + 1
        self.comment = ""
        self.variations: List[MoveNode] = []
        return
    
    def is_null(self) -> bool:
        return False
    
    def is_leaf(self) -> bool:
        return not bool(self.variations)
    
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
    
    def add_comment(self, comment: str) -> None:
        self.comment = "".join((self.comment, comment))
        return
    
    def next(self) -> MoveNode:
        return self.variations[0] if self.variations else self
    
    def prev(self) -> MoveNode:
        return self.parent if not self.parent.is_null() else self
    
    def start(self) -> MoveNode:
        node = self
        while not node.parent.is_null():
            node = node.parent
        return node
    
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
    """A NullMoveNode is sometimes needed, e.g. to detect the root of
    the movetree which can have a NullMoveNode as its parent.
    """
    def __init__(self, move: Move = NullMove(),
            parent: Optional[MoveNode] = None
            ) -> None:
        self.move = NullMove()
        self.parent: MoveNode = self
        self.movenum = 0
        self.comment = ""
        self.variations: List[MoveNode] = []
        return
    
    def is_null(self) -> bool:
        return True


class GameNode(MoveNode):
    """The root node of a movetree. Contains extra information like
    the starting position (handicap/nonstandard game, or a problem
    position) and the player names.
    """
    def __init__(self) -> None:
        super().__init__()
        self.sente = ""
        self.gote = ""
        self.handicap = ""
        self.start_pos = "" # sfen
        return
    
    def __str__(self) -> str:
        acc: List[str] = []
        self._rec_str(acc, MoveNode._str_move)
        return " ".join(acc)
    
    def to_latin(self) -> str:
        acc: List[str] = []
        self._rec_str(acc, MoveNode._latin_move)
        return " ".join(acc)
    
    def to_epd(self, epd_delimiter: str = ";", move_delimiter: str = ","
            ) -> str:
        # Return EPD string (one line) containing start FEN and moves
        acc: List[str] = []
        self._rec_str(acc, MoveNode._str_move)
        return epd_delimiter.join((self.start_pos, move_delimiter.join(acc)))
