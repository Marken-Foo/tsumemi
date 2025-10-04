import pytest

from tsumemi.src.shogi.basetypes import KomaType


@pytest.mark.parametrize(
    "ktype, promoted",
    [
        (KomaType.FU, KomaType.TO),
        (KomaType.KY, KomaType.NY),
        (KomaType.KE, KomaType.NK),
        (KomaType.GI, KomaType.NG),
        (KomaType.KA, KomaType.UM),
        (KomaType.HI, KomaType.RY),
    ],
)
def test_komatype_promotes(ktype: KomaType, promoted: KomaType):
    assert ktype.promote() == promoted


@pytest.mark.parametrize(
    "ktype",
    [
        KomaType.KI,
        KomaType.OU,
        KomaType.TO,
        KomaType.NY,
        KomaType.NK,
        KomaType.NG,
        KomaType.UM,
        KomaType.RY,
    ],
)
def test_komatype_does_not_promote(ktype: KomaType):
    assert ktype.promote() == ktype


@pytest.mark.parametrize(
    "ktype, unpromoted",
    [
        (KomaType.TO, KomaType.FU),
        (KomaType.NY, KomaType.KY),
        (KomaType.NK, KomaType.KE),
        (KomaType.NG, KomaType.GI),
        (KomaType.UM, KomaType.KA),
        (KomaType.RY, KomaType.HI),
    ],
)
def test_komatype_unpromotes(ktype: KomaType, unpromoted: KomaType):
    assert ktype.unpromote() == unpromoted


@pytest.mark.parametrize(
    "ktype",
    [
        KomaType.FU,
        KomaType.KY,
        KomaType.KE,
        KomaType.GI,
        KomaType.KI,
        KomaType.KA,
        KomaType.HI,
        KomaType.OU,
    ],
)
def test_komatype_does_not_unnpromote(ktype: KomaType):
    assert ktype.unpromote() == ktype


@pytest.mark.parametrize(
    "ktype, is_promoted",
    [
        (KomaType.FU, False),
        (KomaType.KY, False),
        (KomaType.KE, False),
        (KomaType.GI, False),
        (KomaType.KI, False),
        (KomaType.KA, False),
        (KomaType.HI, False),
        (KomaType.OU, False),
        (KomaType.TO, True),
        (KomaType.NY, True),
        (KomaType.NK, True),
        (KomaType.NG, True),
        (KomaType.UM, True),
        (KomaType.RY, True),
    ],
)
def test_is_promoted(ktype: KomaType, is_promoted: bool):
    assert ktype.is_promoted() == is_promoted


@pytest.mark.parametrize(
    "ktype, csa",
    [
        (KomaType.FU, "FU"),
        (KomaType.KY, "KY"),
        (KomaType.KE, "KE"),
        (KomaType.GI, "GI"),
        (KomaType.KI, "KI"),
        (KomaType.KA, "KA"),
        (KomaType.HI, "HI"),
        (KomaType.OU, "OU"),
        (KomaType.TO, "TO"),
        (KomaType.NY, "NY"),
        (KomaType.NK, "NK"),
        (KomaType.NG, "NG"),
        (KomaType.UM, "UM"),
        (KomaType.RY, "RY"),
    ],
)
def test_to_csa(ktype: KomaType, csa: str):
    assert ktype.to_csa() == csa
