import pytest

from hypothesis import assume, given, strategies as st

from tsumemi.src.shogi.basetypes import GameTermination, Koma, KomaType, Side
from tsumemi.src.shogi.move import Move, TerminationMove
from tsumemi.src.shogi.position import Position
from tsumemi.src.shogi.square import Square

HAND_KTYPES = [
    KomaType.HI,
    KomaType.KA,
    KomaType.KI,
    KomaType.GI,
    KomaType.KE,
    KomaType.KY,
    KomaType.FU,
]

HAND_MAX_AMOUNT = 18


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


@given(
    board_square(), board_square(), koma(), st.one_of(koma(), st.none()), st.booleans()
)
def test_create_move(
    start_sq: Square,
    end_sq: Square,
    start_koma: Koma,
    end_koma: Koma | None,
    is_promotion: bool,
):
    assume(start_sq != end_sq)
    sut = Position()
    sut.set_koma(start_koma, start_sq)
    if end_koma is not None:
        sut.set_koma(end_koma, end_sq)
    expected = Move(
        start_sq=start_sq,
        end_sq=end_sq,
        is_promotion=is_promotion,
        koma=start_koma,
        captured=Koma.NONE if end_koma is None else end_koma,
    )
    actual = sut.create_move(
        start_sq=start_sq, end_sq=end_sq, is_promotion=is_promotion
    )
    assert actual == expected


@given(board_square(), st.sampled_from(Side), st.sampled_from(HAND_KTYPES))
def test_create_drop_move(end_sq: Square, side: Side, ktype: KomaType):
    sut = Position()
    actual = sut.create_drop_move(side, ktype, end_sq)
    expected = Move(start_sq=Square.HAND, end_sq=end_sq, koma=Koma.make(side, ktype))
    assert actual == expected


def test_make_pass_move():
    pos = Position()
    initial_pieces = pos.get_koma_sets()
    initial_movenum = pos.movenum
    move = TerminationMove(GameTermination.MATE)
    pos.make_move(move)
    final_pieces = pos.get_koma_sets()
    final_movenum = pos.movenum
    assert final_pieces == initial_pieces
    assert final_movenum == initial_movenum + 1


@given(
    board_square(),
    st.sampled_from(Side),
    st.sampled_from(HAND_KTYPES),
    st.integers(1, HAND_MAX_AMOUNT),
)
def test_make_drop_move(end_sq: Square, side: Side, ktype: KomaType, n: int):
    pos = Position()
    pos.set_hand_koma_count(side, ktype, n)
    pos.turn = side
    initial_movenum = pos.movenum
    initial_hand_amount = pos.get_hand_koma_count(side, ktype)
    move = Move(start_sq=Square.HAND, end_sq=end_sq, koma=Koma.make(side, ktype))
    pos.make_move(move)
    final_movenum = pos.movenum
    final_turn = pos.turn
    final_hand_amount = pos.get_hand_koma_count(side, ktype)
    assert final_movenum == initial_movenum + 1
    assert final_turn == side.switch()
    assert final_hand_amount == initial_hand_amount - 1


def test_unmake_pass_move():
    pos = Position()
    initial_pieces = pos.get_koma_sets()
    initial_movenum = pos.movenum
    move = TerminationMove(GameTermination.MATE)
    pos.unmake_move(move)
    final_pieces = pos.get_koma_sets()
    final_movenum = pos.movenum
    assert final_pieces == initial_pieces
    assert final_movenum == initial_movenum - 1


@pytest.mark.parametrize(
    "sfen",
    [
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        "nk1n5/1g3g3/p8/2BP5/3+r5/9/9/9/9 b RBGg4s2n4l16p 17",
    ],
)
def test_starting_position_sfen_roundtrip(sfen: str):
    pos = Position()
    pos.from_sfen(sfen)
    assert pos.to_sfen() == sfen
