from hypothesis import assume, given, strategies as st

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side
from tsumemi.src.shogi.position import Position
from tsumemi.src.shogi.square import Square


@st.composite
def board_square(draw: st.DrawFn) -> Square:
    sq = draw(st.sampled_from(Square))
    assume(sq != Square.NONE and sq != Square.HAND)
    return sq


@st.composite
def koma(draw: st.DrawFn) -> Koma:
    side = draw(st.sampled_from(Side))
    ktype = draw(st.sampled_from(KomaType))
    assume(ktype != KomaType.NONE and ktype != KomaType(13))
    return Koma.make(side, ktype)


@given(koma(), board_square())
def test_set_koma(koma: Koma, sq: Square):
    pos = Position()
    pos.set_koma(koma, sq)
    assert pos.get_koma(sq) == koma


@given(board_square())
def test_initial_board_is_empty(sq: Square):
    pos = Position()
    assert pos.get_koma(sq) == Koma.NONE


@given(st.dictionaries(board_square(), koma()))
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
