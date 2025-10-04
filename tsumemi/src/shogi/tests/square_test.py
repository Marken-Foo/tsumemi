import pytest

from tsumemi.src.shogi.basetypes import Side
from tsumemi.src.shogi.square import Square


@pytest.mark.parametrize("sq", [Square.b11, Square.b72, Square.b43])
def test_row_1_to_3_in_sente_promotion_zone(sq: Square):
    assert sq.is_in_promotion_zone(Side.SENTE)


@pytest.mark.parametrize("sq", [Square.b27, Square.b88, Square.b69])
def test_row_7_to_9_in_gote_promotion_zone(sq: Square):
    assert sq.is_in_promotion_zone(Side.GOTE)


@pytest.mark.parametrize("sq", [Square.b27, Square.b88, Square.b69])
def test_row_7_to_9_not_in_sente_promotion_zone(sq: Square):
    assert not sq.is_in_promotion_zone(Side.SENTE)


@pytest.mark.parametrize("sq", [Square.b11, Square.b72, Square.b43])
def test_row_1_to_3_not_in_gote_promotion_zone(sq: Square):
    assert not sq.is_in_promotion_zone(Side.GOTE)


@pytest.mark.parametrize(
    "sq1, sq2", [(Square.b11, Square.b31), (Square.b14, Square.b94)]
)
def test_is_same_row(sq1: Square, sq2: Square):
    assert sq1.is_same_row(sq2)
