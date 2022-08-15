from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.position import Position

if TYPE_CHECKING:
    from tkinter import ttk
    from tsumemi.src.shogi.notation_writer import AbstractMoveWriter
    from tsumemi.src.tsumemi.game.game_model import GameModel


class MovelistViewModel:
    def __init__(self, game: GameModel, move_writer: AbstractMoveWriter
        ) -> None:
        self.game = game
        self.move_writer = move_writer
        return

    def populate_treeview(self, tvw: ttk.Treeview) -> None:
        displayed_nodes = self.game.get_current_mainline()
        sfen = self.game.get_initial_sfen()
        if not sfen:
            return
        pos = Position()
        pos.from_sfen(sfen)

        for node in displayed_nodes:
            move_num = node.movenum
            move_str = node.write_move(self.move_writer, pos)
            pos.make_move(node.move)
            variation_indicator = "+" if len(node.parent.variations) > 1 else ""
            tvw.insert(
                "", "end", iid=str(node.id),
                values=(str(move_num), move_str, variation_indicator)
            )
        return

    def populate_variation_treeview(self, tvw: ttk.Treeview) -> None:
        # Prints variations available for next move.
        pos = self.game.get_position()
        variations = self.game.get_current_variation_nodes()
        if len(variations) <= 1:
            return
        for i, node in enumerate(variations):
            move_str = node.write_move(self.move_writer, pos)
            tvw.insert("", "end", iid=str(node.id), values=(str(i+1), move_str))
        return

    def go_to_id(self, id_: int) -> None:
        self.game.go_to_id(id_)
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
