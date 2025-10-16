from hypothesis import given, strategies as st

from tsumemi.src.shogi.basetypes import Side
from tsumemi.src.shogi.square import Square


FULL_WIDTH_NUMBERS = {
    0: "０",
    1: "１",
    2: "２",
    3: "３",
    4: "４",
    5: "５",
    6: "６",
    7: "７",
    8: "８",
    9: "９",
}

KANJI_NUMBERS = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
}


@st.composite
def board_squares(draw: st.DrawFn) -> Square:
    row_num = draw(st.integers(1, 9))
    col_num = draw(st.integers(1, 9))
    return Square.from_cr(col_num, row_num)


@given(board_squares())
def test_square_name_matches_cr(sq: Square):
    (col, row) = sq.get_cr()
    assert sq == Square[f"b{col}{row}"].value


@given(board_squares())
def test_cr_square_roundtrip(sq: Square):
    (col, row) = sq.get_cr()
    new_sq = Square.from_cr(col, row)
    assert sq == new_sq


@given(st.sampled_from(Square))
def test_fixed_row_1_to_3_in_sente_promotion_zone(sq: Square):
    (_, row) = sq.get_cr()
    assert sq.is_in_promotion_zone(Side.SENTE) == (1 <= row <= 3)


@given(st.sampled_from(Square))
def test_row_7_to_9_in_gote_promotion_zone(sq: Square):
    (_, row) = sq.get_cr()
    assert sq.is_in_promotion_zone(Side.GOTE) == (7 <= row <= 9)


@given(board_squares(), board_squares())
def test_is_same_row(sq1: Square, sq2: Square):
    (_, row1) = sq1.get_cr()
    (_, row2) = sq2.get_cr()
    assert sq1.is_same_row(sq2) == sq2.is_same_row(sq1) == (row1 == row2)


@given(board_squares())
def test_to_japanese(sq: Square):
    (col, row) = sq.get_cr()
    assert sq.to_japanese() == f"{FULL_WIDTH_NUMBERS[col]}{KANJI_NUMBERS[row]}"
