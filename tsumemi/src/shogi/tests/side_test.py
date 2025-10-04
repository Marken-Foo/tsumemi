from tsumemi.src.shogi.basetypes import Side


def test_handicap_sides_equal_normal_sides():
    assert Side.UWATE == Side.GOTE
    assert Side.SHITATE == Side.SENTE


def test_switch():
    assert Side.SENTE.switch() == Side.GOTE
    assert Side.GOTE.switch() == Side.SENTE
