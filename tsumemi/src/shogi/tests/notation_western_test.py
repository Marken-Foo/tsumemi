from __future__ import annotations

from hypothesis import given, strategies as st
import pytest

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import Koma, SFEN_FROM_KOMA, Side
from tsumemi.src.shogi.notation import WesternMoveWriter
from tsumemi.src.shogi.position import Position
from tsumemi.src.shogi.tests.notation_test import (
    get_parametrization_from_test_cases,
    read_notation_test_file,
)
from tsumemi.src.shogi.tests.position_hand_test import TEST_HAND_KTYPES
from tsumemi.src.shogi.tests.square_test import board_squares

if TYPE_CHECKING:
    from tsumemi.src.shogi.basetypes import KomaType
    from tsumemi.src.shogi.square import Square


western_notation_test_cases = read_notation_test_file(
    r"tsumemi/src/shogi/tests/notation_test_cases_western.txt"
)

western_args, western_names = get_parametrization_from_test_cases(
    western_notation_test_cases
)


@pytest.mark.parametrize(
    ["koma_locations", "start_sq", "end_sq", "is_promotion", "expected"],
    western_args,
    ids=western_names,
)
def test_western_notation(
    koma_locations: list[tuple[Square, Koma]],
    start_sq: Square,
    end_sq: Square,
    is_promotion: bool,
    expected: str,
):
    move_writer = WesternMoveWriter()
    pos = Position()
    for square, koma in koma_locations:
        pos.set_koma(koma, square)
    move = pos.create_move(start_sq=start_sq, end_sq=end_sq, is_promotion=is_promotion)
    assert move_writer.write_move(move, pos) == expected


@given(
    board_squares(),
    st.sampled_from(TEST_HAND_KTYPES),
    st.sampled_from([Side.SENTE, Side.GOTE]),
)
def test_western_drop(sq: Square, ktype: KomaType, side: Side):
    move_writer = WesternMoveWriter()
    pos = Position()
    pos.set_hand_koma_count(side, ktype, 1)
    move = pos.create_drop_move(side, ktype, sq)
    col, row = sq.get_cr()
    assert (
        move_writer.write_move(move, pos)
        == f"{SFEN_FROM_KOMA[Koma.make(side, ktype)].upper()}*{col}{row}"
    )
