from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.game import Game

if TYPE_CHECKING:
    import typing
    from typing import Sequence
    from tsumemi.src.shogi.basetypes import Move


class ParserVisitor:
    # the idea is that a kif_reader/sfen_reader/csa_reader can accept
    # the same visitor, which holds diff methods for diff readers.
    def __init__(self) -> None:
        return

    def visit_board(self, reader: Reader, lines: Sequence[str]) -> None:
        pass

    def visit_comment(self, reader: Reader, line: str) -> None:
        pass

    def visit_escape(self, reader: Reader, line: str) -> None:
        pass

    def visit_handicap(self, reader: Reader, handicap_sfen: str) -> None:
        pass

    def visit_move(self, reader: Reader, move: Move) -> None:
        pass

    def visit_variation(self, reader: Reader, line: str) -> None:
        pass


class GameBuilderPVis(ParserVisitor):
    def __init__(self) -> None:
        super().__init__()
        return

    def visit_handicap(self, reader: Reader, handicap_sfen: str) -> None:
        pos = reader.game.position
        movetree = reader.game.movetree
        pos.from_sfen(handicap_sfen)
        movetree.handicap = handicap_sfen
        movetree.start_pos = handicap_sfen
        return

    def visit_move(self, reader: Reader, move: Move) -> None:
        game = reader.game
        game.add_move(move)
        return


class Reader:
    def __init__(self) -> None:
        self.game = Game()
        return

    def read(self, handle: typing.TextIO, visitor: ParserVisitor) -> Game:
        return self.game
