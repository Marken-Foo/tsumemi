import pytest

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side


@pytest.mark.parametrize(
    "side, ktype",
    [
        (Side.SENTE, KomaType.FU),
        (Side.SENTE, KomaType.NK),
        (Side.GOTE, KomaType.UM),
        (Side.GOTE, KomaType.KI),
    ],
)
def test_get_side(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.side() == side


@pytest.mark.parametrize(
    "side, ktype",
    [
        (Side.SENTE, KomaType.FU),
        (Side.SENTE, KomaType.NK),
        (Side.GOTE, KomaType.UM),
        (Side.GOTE, KomaType.KI),
    ],
)
def test_get_komatype(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert KomaType.get(koma) == ktype


@pytest.mark.parametrize(
    "side, ktype",
    [
        (Side.SENTE, KomaType.FU),
        (Side.SENTE, KomaType.NK),
        (Side.GOTE, KomaType.UM),
        (Side.GOTE, KomaType.KI),
        (Side.SENTE, KomaType.OU),
    ],
)
def test_promote(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.promote() == Koma.make(side, ktype.promote())


@pytest.mark.parametrize(
    "side, ktype",
    [
        (Side.SENTE, KomaType.FU),
        (Side.SENTE, KomaType.NK),
        (Side.GOTE, KomaType.UM),
        (Side.GOTE, KomaType.KI),
        (Side.SENTE, KomaType.OU),
    ],
)
def test_is_promoted(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.is_promoted() == ktype.is_promoted()
