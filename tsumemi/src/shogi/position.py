from __future__ import annotations

import re

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side
from tsumemi.src.shogi.basetypes import KOMA_FROM_SFEN
from tsumemi.src.shogi.move import Move
from tsumemi.src.shogi.square import Square
from tsumemi.src.shogi.position_internals import (
    HandRepresentation,
    MailboxBoard,
)

if TYPE_CHECKING:
    from typing import Any
    from tsumemi.src.shogi.position_internals import KomaLocations, KomasBySquare


class Position:
    """Represents a shogi position, including board position, side to
    move, and pieces in hand.
    """

    def __init__(self) -> None:
        self.board = MailboxBoard()
        self.hand_sente = HandRepresentation()
        self.hand_gote = HandRepresentation()
        self.turn = Side.SENTE
        self.movenum = 1

    def __str__(self) -> str:
        elems = [
            str(self.board),
            "Sente hand:",
            str(self.hand_sente),
            "Gote hand:",
            str(self.hand_gote),
            "Turn: Sente" if self.turn == Side.SENTE else "Turn: Gote",
        ]
        return "\n".join(elems)

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Position)
            and self.get_komas_by_square() == other.get_komas_by_square()
            and self.get_hand_of_side(Side.SENTE) == other.get_hand_of_side(Side.SENTE)
            and self.get_hand_of_side(Side.GOTE) == other.get_hand_of_side(Side.GOTE)
            and self.turn == other.turn
        )

    def reset(self) -> None:
        self.board.reset()
        self.hand_sente.reset()
        self.hand_gote.reset()
        self.turn = Side.SENTE
        self.movenum = 1

    def get_hand_of_side(self, side: Side) -> HandRepresentation:
        return self.hand_sente if side is Side.SENTE else self.hand_gote

    def set_hand_koma_count(self, side: Side, ktype: KomaType, count: int) -> None:
        hand = self.get_hand_of_side(side)
        hand.set_komatype_count(ktype, count)

    def get_hand_koma_count(self, side: Side, ktype: KomaType) -> int:
        hand = self.get_hand_of_side(side)
        return hand.get_komatype_count(ktype)

    def inc_hand_koma(self, side: Side, ktype: KomaType) -> None:
        hand = self.get_hand_of_side(side)
        hand.inc_komatype(ktype)

    def dec_hand_koma(self, side: Side, ktype: KomaType) -> None:
        hand = self.get_hand_of_side(side)
        hand.dec_komatype(ktype)

    def is_hand_empty(self, side: Side) -> bool:
        return self.get_hand_of_side(side).is_empty()

    def set_koma(self, koma: Koma, sq: Square) -> None:
        return self.board.set_koma(koma, sq)

    def get_koma(self, sq: Square) -> Koma:
        return self.board.get_koma(sq)

    def get_koma_sets(self) -> KomaLocations:
        return self.board.get_koma_sets()

    def get_komas_by_square(self) -> KomasBySquare:
        return self.board.get_komas_by_square()

    def create_move(
        self, start_sq: Square, end_sq: Square, is_promotion: bool = False
    ) -> Move:
        """Creates a move from two squares. Move need not necessarily
        be legal or even valid.
        """
        return Move(
            start_sq=start_sq,
            end_sq=end_sq,
            is_promotion=is_promotion,
            koma=self.get_koma(start_sq),
            captured=self.get_koma(end_sq),
        )

    def create_drop_move(self, side: Side, ktype: KomaType, end_sq: Square) -> Move:
        """Creates a drop Move. Move need not necessarily be legal or
        even valid.
        """
        return Move(start_sq=Square.HAND, end_sq=end_sq, koma=Koma.make(side, ktype))

    def make_move(self, move: Move) -> None:
        """Makes a move on the board."""
        if move.is_null():
            return
        if move.is_pass():
            # to account for game terminations or other passing moves
            self.movenum += 1
        elif move.is_drop:
            self.dec_hand_koma(move.side, KomaType.get(move.koma))
            self.set_koma(move.koma, move.end_sq)
            self.turn = self.turn.switch()
            self.movenum += 1
        else:
            self.set_koma(Koma.NONE, move.start_sq)
            if move.captured != Koma.NONE:
                self.inc_hand_koma(move.side, KomaType.get(move.captured).unpromote())
            self.set_koma(
                move.koma.promote() if move.is_promotion else move.koma, move.end_sq
            )
            self.turn = self.turn.switch()
            self.movenum += 1

    def unmake_move(self, move: Move) -> None:
        """Unplays/retracts a move from the board."""
        if move.is_pass():
            self.movenum -= 1
        elif move.is_drop:
            self.set_koma(Koma.NONE, move.end_sq)
            self.inc_hand_koma(move.side, KomaType.get(move.koma))
            self.turn = self.turn.switch()
            self.movenum -= 1
        else:
            if move.captured != Koma.NONE:
                self.dec_hand_koma(move.side, KomaType.get(move.captured).unpromote())
            self.set_koma(move.captured, move.end_sq)
            self.set_koma(move.koma, move.start_sq)
            self.turn = self.turn.switch()
            self.movenum -= 1

    def to_sfen(self) -> str:
        """Return SFEN string representing the current position."""
        sfen_board = self.board.to_sfen()
        sfen_turn = "b" if self.turn is Side.SENTE else "w"
        if self.hand_sente.is_empty() and self.hand_gote.is_empty():
            sfen_hands = "-"
        else:
            sfen_hands = "".join(
                (self.hand_sente.to_sfen(), self.hand_gote.to_sfen().lower())
            )
        sfen_move_num = str(self.movenum)
        return " ".join((sfen_board, sfen_turn, sfen_hands, sfen_move_num))

    def from_sfen(self, sfen: str) -> None:
        """Parse an SFEN string and set up the position it represents."""
        sfen_board, sfen_turn, sfen_hands, sfen_move_num = sfen.split(" ")
        self.reset()
        if sfen_turn == "b":
            self.turn = Side.SENTE
        elif sfen_turn == "w":
            self.turn = Side.GOTE
        else:
            # This is possibly too strict
            raise ValueError("SFEN contains unknown side to move")
        try:
            self.movenum = int(sfen_move_num)
        except ValueError as exc:
            raise ValueError(
                f"SFEN contains unknown movenumber '{sfen_move_num}'"
            ) from exc
        try:
            self._parse_sfen_board(sfen_board)
            self._parse_sfen_hands(sfen_hands)
        except ValueError as exc:
            raise ValueError(f"Invalid SFEN: '{sfen}'") from exc

    def _parse_sfen_hands(self, sfen_hands: str) -> None:
        it_hands = re.findall(r"(\d*)([plnsgbrPLNSGBR])", sfen_hands)
        for ch_count, ch in it_hands:
            try:
                koma = KOMA_FROM_SFEN[ch]
            except KeyError as exc:
                raise ValueError(f"SFEN contains unknown character '{ch}'") from exc
            ktype = KomaType.get(koma)
            target_hand = self.hand_sente if ch.isupper() else self.hand_gote
            count = int(ch_count) if ch_count else 1
            target_hand.set_komatype_count(ktype, count)

    def _parse_sfen_board(self, sfen_board: str) -> None:
        # Parses the part of an SFEN string representing the board.
        rows = sfen_board.split("/")
        if len(rows) != 9:
            raise ValueError("SFEN board has wrong number of rows")
        for i, row in enumerate(rows):
            self._parse_sfen_board_row(row, i + 1)

    def _parse_sfen_board_row(self, sfen_row: str, row_num: int) -> None:
        # Parses one row of an SFEN board string.
        col_num = 9
        promotion_flag = False
        for ch in sfen_row:
            if col_num <= 0:
                raise ValueError("SFEN row has wrong length")
            if ch.isdigit():
                if promotion_flag:
                    raise ValueError("Digit cannot follow + in SFEN")
                col_num -= int(ch)
                continue
            if ch == "+":
                if promotion_flag:
                    raise ValueError("+ cannot follow + in SFEN")
                promotion_flag = True
                continue
            # This line has the intended side effects
            self._set_koma_from_sfen(ch, col_num, row_num, promotion_flag)
            promotion_flag = False
            col_num -= 1
        if col_num != 0:
            raise ValueError("SFEN row has wrong length")
        if promotion_flag:
            raise ValueError("SFEN row cannot end with +")

    def _set_koma_from_sfen(
        self, ch: str, col_num: int, row_num: int, promotion_flag: bool
    ) -> None:
        try:
            koma = KOMA_FROM_SFEN[ch]
        except KeyError as exc:
            raise ValueError(f"SFEN contains unknown character '{ch}'") from exc
        sq = Square.from_cr(col_num=col_num, row_num=row_num)
        if promotion_flag:
            koma = koma.promote()
        self.set_koma(koma, sq)
