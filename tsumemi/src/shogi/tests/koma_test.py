from hypothesis import given, strategies as st

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side


@given(st.sampled_from(Side), st.sampled_from(KomaType))
def test_get_side(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.side() == side


@given(st.sampled_from(Side), st.sampled_from(KomaType))
def test_get_komatype(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert KomaType.get(koma) == ktype


@given(st.sampled_from(Side), st.sampled_from(KomaType))
def test_promote(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.promote() == Koma.make(side, ktype.promote())


@given(st.sampled_from(Side), st.sampled_from(KomaType))
def test_is_promoted(side: Side, ktype: KomaType):
    koma = Koma.make(side, ktype)
    assert koma.is_promoted() == ktype.is_promoted()
