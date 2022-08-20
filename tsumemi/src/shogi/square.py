from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Tuple
    from tsumemi.src.shogi.basetypes import Side


class KanjiNumber(IntEnum):
    一 = 1
    二 = 2
    三 = 3
    四 = 4
    五 = 5
    六 = 6
    七 = 7
    八 = 8
    九 = 9
    十 = 10


FULL_WIDTH_NUMBER: Dict[int, str] = {
    0: "０", 1: "１", 2: "２", 3: "３", 4: "４",
    5: "５", 6: "６", 7: "７", 8: "８", 9: "９"
}


class Square(IntEnum):
    """Represents a square on the shogi board, or a piecetype in hand.
    """
    NONE = 0
    HAND = 82
    b11, b12, b13, b14, b15, b16, b17, b18, b19 = range(1, 10)
    b21, b22, b23, b24, b25, b26, b27, b28, b29 = range(10, 19)
    b31, b32, b33, b34, b35, b36, b37, b38, b39 = range(19, 28)
    b41, b42, b43, b44, b45, b46, b47, b48, b49 = range(28, 37)
    b51, b52, b53, b54, b55, b56, b57, b58, b59 = range(37, 46)
    b61, b62, b63, b64, b65, b66, b67, b68, b69 = range(46, 55)
    b71, b72, b73, b74, b75, b76, b77, b78, b79 = range(55, 64)
    b81, b82, b83, b84, b85, b86, b87, b88, b89 = range(64, 73)
    b91, b92, b93, b94, b95, b96, b97, b98, b99 = range(73, 82)

    def __str__(self) -> str:
        col, row = self.get_cr()
        return str(10*col+row)

    @classmethod
    def from_cr(cls, col_num: int, row_num: int) -> Square:
        return cls(9*col_num-9+row_num)

    @classmethod
    def from_coord(cls, coord: int) -> Square:
        return cls.from_cr(col_num=int(coord/10), row_num=coord%10)

    def get_cr(self) -> Tuple[int, int]:
        col = (self-1)// 9 + 1
        row = (self-1) % 9 + 1
        return col, row

    def is_board(self) -> bool:
        return self.name.startswith("b")

    def is_hand(self) -> bool:
        return self == Square.HAND

    def is_in_promotion_zone(self, side: Side) -> bool:
        _, row = self.get_cr()
        return row in (1, 2, 3) if side.is_sente() else row in (7, 8, 9)

    def is_in_last_two_rows(self, side: Side) -> bool:
        _, row = self.get_cr()
        return row in (1, 2) if side.is_sente() else row in (8, 9)

    def is_in_last_row(self, side: Side) -> bool:
        _, row = self.get_cr()
        return row == 1 if side.is_sente() else row == 9

    def is_left_of(self, sq_other: Square, side: Side) -> bool:
        col_diff, _ = self._subtract_squares(sq_other)
        return col_diff > 0 if side.is_sente() else col_diff < 0

    def is_right_of(self, sq_other: Square, side: Side) -> bool:
        return sq_other.is_left_of(self, side)

    def is_forward_of(self, sq_other: Square, side: Side) -> bool:
        _, row_diff = self._subtract_squares(sq_other)
        return row_diff < 0 if side.is_sente() else row_diff > 0

    def is_backward_of(self, sq_other: Square, side: Side) -> bool:
        return sq_other.is_forward_of(self, side)

    def is_same_row(self, sq_other: Square) -> bool:
        _, row_diff = self._subtract_squares(sq_other)
        return row_diff == 0

    def _subtract_squares(self, sq_other: Square) -> Tuple[int, int]:
        col, row = self.get_cr()
        col_other, row_other = sq_other.get_cr()
        return (col - col_other, row - row_other)

    def is_immediately_forward_of(self, sq_other: Square, side: Side) -> bool:
        forward = -1 if side.is_sente() else 1
        return self._subtract_squares(sq_other) == (0, forward)

    def to_japanese(self) -> str:
        col, row = self.get_cr()
        return FULL_WIDTH_NUMBER[col] + KanjiNumber(row).name
