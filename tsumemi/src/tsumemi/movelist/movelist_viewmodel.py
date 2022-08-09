from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.game import Game

if TYPE_CHECKING:
    from tsumemi.src.shogi.notation_writer import AbstractMoveWriter
    from tsumemi.src.tsumemi.movelist.movelist_view import MovelistTreeview


class MovelistViewModel:
    def __init__(self, game: Game, move_writer: AbstractMoveWriter) -> None:
        self.game = game
        self.move_writer = move_writer
        return

    def populate_treeview(self, tvw: MovelistTreeview) -> None:
        mainline_nodes = self.game.movetree.traverse_mainline()
        for node in mainline_nodes:
            move_num = node.movenum
            move_str = (
                ""
                if node.move.is_null()
                else self.move_writer.write_move(
                    node.move, self.game.position, False
                ))
            variation_indicator = "*" if len(node.variations) > 1 else ""
            move_display_str = "".join((
                str(move_num), "　", move_str, variation_indicator
            ))
            tvw.insert(
                "", "end", iid=str(node.id),
                values=(move_display_str,)
            )
        return
