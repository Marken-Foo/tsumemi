from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsumemi.src.shogi.notation_writer import AbstractMoveWriter
    from tsumemi.src.tsumemi.game.game_model import GameModel
    from tsumemi.src.tsumemi.movelist.movelist_view import MovelistTreeview


class MovelistViewModel:
    def __init__(self, game: GameModel, move_writer: AbstractMoveWriter
        ) -> None:
        self.game = game
        self.move_writer = move_writer
        return

    def populate_treeview(self, tvw: MovelistTreeview) -> None:
        mainline_nodes = self.game.game.movetree.traverse_mainline()
        for node in mainline_nodes:
            move_num = node.movenum
            move_str = (
                ""
                if node.move.is_null()
                else self.move_writer.write_move(
                    node.move, self.game.get_position(), False
                ))
            variation_indicator = "+" if len(node.parent.variations) > 1 else ""
            tvw.insert(
                "", "end", iid=str(node.id),
                values=(str(move_num), move_str, variation_indicator)
            )
        return

    def go_to_id(self, _id: int) -> None:
        self.game.go_to_id(_id)
        return

    def go_to_start(self) -> None:
        self.game.go_to_start()
        return

    def go_to_end(self) -> None:
        self.game.go_to_end()
        return

    def go_next(self) -> None:
        self.game.go_next_move()
        return

    def go_prev(self) -> None:
        self.game.go_prev_move()
        return
