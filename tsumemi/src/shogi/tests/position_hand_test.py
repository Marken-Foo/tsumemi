from hypothesis import given, strategies as st

from tsumemi.src.shogi.basetypes import KomaType, Side
from tsumemi.src.shogi.position import Position

TEST_HAND_KTYPES = [
    KomaType.HI,
    KomaType.KA,
    KomaType.KI,
    KomaType.GI,
    KomaType.KE,
    KomaType.KY,
    KomaType.FU,
]

TEST_HAND_MAX_AMOUNT = 18


def random_hand() -> st.SearchStrategy[dict[KomaType, int]]:
    return st.dictionaries(
        st.sampled_from(TEST_HAND_KTYPES), st.integers(0, TEST_HAND_MAX_AMOUNT)
    )


@given(random_hand(), st.sampled_from(Side))
def test_is_hand_empty(hand_dict: dict[KomaType, int], side: Side):
    pos = Position()
    for ktype, amount in hand_dict.items():
        pos.set_hand_koma_count(side, ktype, amount)
    assert pos.is_hand_empty(side) == all(
        (lambda v: v == 0)(value) for value in hand_dict.values()
    )


def test_initial_hands_empty():
    pos = Position()
    assert pos.is_hand_empty(Side.SENTE)
    assert pos.is_hand_empty(Side.GOTE)


@given(
    st.sampled_from(TEST_HAND_KTYPES),
    st.integers(0, TEST_HAND_MAX_AMOUNT),
    st.sampled_from(Side),
)
def test_set_hand_koma_count(ktype: KomaType, amount: int, side: Side):
    pos = Position()
    pos.set_hand_koma_count(side, ktype, amount)
    assert pos.get_hand_koma_count(side, ktype) == amount


@given(
    st.sampled_from(TEST_HAND_KTYPES),
    st.integers(0, TEST_HAND_MAX_AMOUNT - 1),
    st.sampled_from(Side),
)
def test_inc_hand_koma(ktype: KomaType, amount: int, side: Side):
    pos = Position()
    pos.set_hand_koma_count(side, ktype, amount)
    pos.inc_hand_koma(side, ktype)
    assert pos.get_hand_koma_count(side, ktype) == amount + 1


@given(
    st.sampled_from(TEST_HAND_KTYPES),
    st.integers(1, TEST_HAND_MAX_AMOUNT),
    st.sampled_from(Side),
)
def test_dec_hand_koma(ktype: KomaType, amount: int, side: Side):
    pos = Position()
    pos.set_hand_koma_count(side, ktype, amount)
    pos.dec_hand_koma(side, ktype)
    assert pos.get_hand_koma_count(side, ktype) == amount - 1


@given(st.sampled_from(TEST_HAND_KTYPES), st.sampled_from(Side))
def test_dec_empty_hand_koma(ktype: KomaType, side: Side):
    pos = Position()
    pos.set_hand_koma_count(side, ktype, 0)
    try:
        pos.dec_hand_koma(side, ktype)
        assert False
    except ValueError:
        pass
