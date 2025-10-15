from hypothesis import assume, given, strategies as st

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side


def valid_side() -> st.SearchStrategy:
    return st.sampled_from([Side.SENTE, Side.GOTE, Side.UWATE, Side.SHITATE])


@st.composite
def valid_koma(draw: st.DrawFn) -> Koma:
    side = draw(valid_side())
    ktype = draw(st.sampled_from(KomaType))
    assume(ktype != KomaType.NONE and ktype != KomaType(13))
    return Koma.make(side, ktype)


@given(valid_side(), st.sampled_from(KomaType))
def test_get_side(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.side() == side


@given(valid_side(), st.sampled_from(KomaType))
def test_get_komatype(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert KomaType.get(koma) == ktype


@given(valid_side(), st.sampled_from(KomaType))
def test_promote(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.promote() == Koma.make(side, ktype.promote())


@given(valid_side(), st.sampled_from(KomaType))
def test_is_promoted(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.is_promoted() == ktype.is_promoted()
