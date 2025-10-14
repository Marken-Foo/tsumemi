from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List
    from tsumemi.src.shogi.game import Game
    from tsumemi.src.shogi.gametree import MoveNode
    from tsumemi.src.shogi.notation.notation import AbstractMoveWriter
    from tsumemi.src.shogi.position import Position


class NotationWriter:
    """Provides a common interface for writing moves in shogi
    notation.
    """

    def __init__(self, move_writer: AbstractMoveWriter) -> None:
        self._move_writer: AbstractMoveWriter = move_writer

    def write_node(self, node: MoveNode, pos: Position) -> str:
        return node.write_move(self._move_writer, pos)

    def write_mainline(self, game: Game) -> List[str]:
        return game.get_mainline_notation(self._move_writer)

    def change_move_writer(self, move_writer: AbstractMoveWriter) -> None:
        self._move_writer = move_writer
