import pytest

from hypothesis import assume, given, strategies as st

from tsumemi.src.shogi.basetypes import GameTermination, Koma, KomaType, Side
from tsumemi.src.shogi.move import Move, TerminationMove
from tsumemi.src.shogi.position import Position
from tsumemi.src.shogi.square import Square
from tsumemi.src.shogi.tests.koma_test import valid_koma
from tsumemi.src.shogi.tests.position_hand_test import (
    TEST_HAND_KTYPES,
    TEST_HAND_MAX_AMOUNT,
)
from tsumemi.src.shogi.tests.square_test import board_squares


@given(
    board_squares(),
    board_squares(),
    valid_koma(),
    st.one_of(valid_koma(), st.none()),
    st.booleans(),
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


@given(board_squares(), st.sampled_from(Side), st.sampled_from(TEST_HAND_KTYPES))
def test_create_drop_move(end_sq: Square, side: Side, ktype: KomaType):
    sut = Position()
    actual = sut.create_drop_move(side, ktype, end_sq)
    expected = Move(start_sq=Square.HAND, end_sq=end_sq, koma=Koma.make(side, ktype))
    assert actual == expected


def test_make_pass_move():
    pos = Position()
    initial_pieces = pos.get_koma_sets()
    initial_sente_hand = pos.get_hand_of_side(Side.SENTE)
    initial_gote_hand = pos.get_hand_of_side(Side.GOTE)
    initial_movenum = pos.movenum
    move = TerminationMove(GameTermination.MATE)
    pos.make_move(move)
    final_pieces = pos.get_koma_sets()
    final_sente_hand = pos.get_hand_of_side(Side.SENTE)
    final_gote_hand = pos.get_hand_of_side(Side.GOTE)
    final_movenum = pos.movenum
    assert final_pieces == initial_pieces
    assert final_sente_hand == initial_sente_hand
    assert final_gote_hand == initial_gote_hand
    assert final_movenum == initial_movenum + 1


@given(
    board_squares(),
    st.sampled_from(Side),
    st.sampled_from(TEST_HAND_KTYPES),
    st.integers(1, TEST_HAND_MAX_AMOUNT),
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
    assert pos.get_koma(end_sq) == Koma.make(side, ktype)


@given(
    board_squares(),
    board_squares(),
    valid_koma(),
    st.one_of(valid_koma(), st.none()),
    st.booleans(),
)
def test_make_move(
    start_sq: Square,
    end_sq: Square,
    start_koma: Koma,
    end_koma: Koma | None,
    is_promotion: bool,
):
    assume(start_sq != end_sq)
    # TODO: Remove this assumption and fix the underlying crash
    if end_koma is not None:
        assume(TEST_HAND_KTYPES.__contains__(KomaType.get(end_koma).unpromote()))
    pos = Position()
    side = start_koma.side()
    pos.turn = side
    initial_movenum = pos.movenum
    initial_hand_amount = (
        -1
        if end_koma is None
        else pos.get_hand_koma_count(side, KomaType.get(end_koma).unpromote())
    )
    pos.set_koma(start_koma, start_sq)
    if end_koma is not None:
        pos.set_koma(end_koma, end_sq)
    move = Move(
        start_sq=start_sq,
        end_sq=end_sq,
        is_promotion=is_promotion,
        koma=start_koma,
        captured=Koma.NONE if end_koma is None else end_koma,
    )
    pos.make_move(move)
    final_movenum = pos.movenum
    final_turn = pos.turn
    assert final_movenum == initial_movenum + 1
    assert final_turn == side.switch()
    assert pos.get_koma(start_sq) == Koma.NONE
    assert pos.get_koma(end_sq) == start_koma.promote() if is_promotion else start_koma
    if end_koma is not None:
        assert (
            pos.get_hand_koma_count(side, KomaType.get(end_koma).unpromote())
            == initial_hand_amount + 1
        )


def test_unmake_pass_move():
    pos = Position()
    initial_pieces = pos.get_koma_sets()
    initial_sente_hand = pos.get_hand_of_side(Side.SENTE)
    initial_gote_hand = pos.get_hand_of_side(Side.GOTE)
    initial_movenum = pos.movenum
    move = TerminationMove(GameTermination.MATE)
    pos.unmake_move(move)
    final_pieces = pos.get_koma_sets()
    final_sente_hand = pos.get_hand_of_side(Side.SENTE)
    final_gote_hand = pos.get_hand_of_side(Side.GOTE)
    final_movenum = pos.movenum
    assert final_pieces == initial_pieces
    assert final_sente_hand == initial_sente_hand
    assert final_gote_hand == initial_gote_hand
    assert final_movenum == initial_movenum - 1


@given(
    board_squares(),
    st.sampled_from(Side),
    st.sampled_from(TEST_HAND_KTYPES),
    st.integers(0, TEST_HAND_MAX_AMOUNT - 1),
)
def test_unmake_drop_move(end_sq: Square, side: Side, ktype: KomaType, n: int):
    pos = Position()
    pos.set_koma(Koma.make(side, ktype), end_sq)
    pos.set_hand_koma_count(side, ktype, n)
    pos.turn = side.switch()
    initial_movenum = pos.movenum
    initial_hand_amount = pos.get_hand_koma_count(side, ktype)
    move = Move(start_sq=Square.HAND, end_sq=end_sq, koma=Koma.make(side, ktype))
    pos.unmake_move(move)
    final_movenum = pos.movenum
    final_turn = pos.turn
    final_hand_amount = pos.get_hand_koma_count(side, ktype)
    assert final_movenum == initial_movenum - 1
    assert final_turn == side
    assert final_hand_amount == initial_hand_amount + 1
    assert pos.get_koma(end_sq) == Koma.NONE


@given(
    board_squares(),
    board_squares(),
    valid_koma(),
    st.one_of(valid_koma(), st.none()),
    st.booleans(),
    st.integers(1, TEST_HAND_MAX_AMOUNT),
)
def test_unmake_move(
    start_sq: Square,
    end_sq: Square,
    start_koma: Koma,
    end_koma: Koma | None,
    is_promotion: bool,
    n: int,
):
    assume(start_sq != end_sq)
    # TODO: Remove this assumption and fix the underlying crash
    if end_koma is not None:
        assume(TEST_HAND_KTYPES.__contains__(KomaType.get(end_koma).unpromote()))
    pos = Position()
    side = start_koma.side()
    if end_koma is not None:
        pos.set_hand_koma_count(side, KomaType.get(end_koma).unpromote(), n)
    pos.turn = side.switch()
    initial_movenum = pos.movenum
    initial_hand_amount = (
        -1
        if end_koma is None
        else pos.get_hand_koma_count(side, KomaType.get(end_koma).unpromote())
    )
    pos.set_koma(start_koma.promote() if is_promotion else start_koma, end_sq)
    move = Move(
        start_sq=start_sq,
        end_sq=end_sq,
        is_promotion=is_promotion,
        koma=start_koma,
        captured=Koma.NONE if end_koma is None else end_koma,
    )
    pos.unmake_move(move)
    final_movenum = pos.movenum
    final_turn = pos.turn
    assert final_movenum == initial_movenum - 1
    assert final_turn == side
    assert pos.get_koma(start_sq) == start_koma
    assert pos.get_koma(end_sq) == Koma.NONE if end_koma is None else end_koma
    if end_koma is not None:
        assert (
            pos.get_hand_koma_count(side, KomaType.get(end_koma).unpromote())
            == initial_hand_amount - 1
        )


@pytest.mark.parametrize(
    "sfen",
    [
        "krbgsnlp1/1+r+b1+s+n+l+p1/9/9/9/9/9/1+P+L+N+S1+B+R1/1PLNSGBRK b - 1",
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        "nk1n5/1g3g3/p8/2BP5/3+r5/9/9/9/9 b RBGg4s2n4l16p 17",
    ],
)
def test_sfen_roundtrip(sfen: str):
    pos = Position()
    pos.from_sfen(sfen)
    assert pos.to_sfen() == sfen
