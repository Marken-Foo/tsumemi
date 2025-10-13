from hypothesis import given, strategies as st

from tsumemi.src.shogi.basetypes import Koma
from tsumemi.src.shogi.position import Position
from tsumemi.src.shogi.square import Square
from tsumemi.src.shogi.tests.koma_test import valid_koma
from tsumemi.src.shogi.tests.square_test import board_squares


@given(valid_koma(), board_squares())
def test_set_koma(koma: Koma, sq: Square):
    pos = Position()
    pos.set_koma(koma, sq)
    assert pos.get_koma(sq) == koma


@given(board_squares())
def test_initial_board_is_empty(sq: Square):
    pos = Position()
    assert pos.get_koma(sq) == Koma.NONE


@given(st.dictionaries(board_squares(), valid_koma()))
def test_get_koma_sets(square_contents: dict[Square, Koma]):
    pos = Position()
    expected: dict[Koma, set[Square]] = {}
    for sq, koma in square_contents.items():
        pos.set_koma(koma, sq)
        new_set = expected.get(koma, set())
        new_set.add(sq)
        expected[koma] = new_set
    sut = pos.get_koma_sets()
    for koma, sq_set in sut.items():
        assert sq_set == expected.get(koma, set())
