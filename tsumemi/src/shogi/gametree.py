from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Optional

if TYPE_CHECKING:
    from tsumemi.src.shogi.basetypes import Move

from tsumemi.src.shogi.basetypes import NullMove


class MoveNode:
    # Node in the gametree
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
