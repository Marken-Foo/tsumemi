import pytest
from collections.abc import Iterable

from tsumemi.src.shogi import rules
from tsumemi.src.shogi.basetypes import KomaType, Side
from tsumemi.src.shogi.position import Position
from tsumemi.src.shogi.tests.rules_movegen_test_cases import MOVEGEN_TEST_CASES


argvalues, names = zip(
    *(((t.ktype, t.sfen, t.expected_moves), t.name) for t in MOVEGEN_TEST_CASES)
)


@pytest.mark.parametrize(
    ["ktype", "sfen", "moves"],
    argvalues,
    ids=names,
)
def test_move_generation(ktype: KomaType, sfen: str, moves: dict[Side, Iterable[str]]):
    pos = Position()
    pos.from_sfen(sfen)
    movelist_sente = rules.generate_valid_moves(pos=pos, side=Side.SENTE, ktype=ktype)
    movelist_gote = rules.generate_valid_moves(pos=pos, side=Side.GOTE, ktype=ktype)
    actual_sente = {move.to_latin() for move in movelist_sente}
    actual_gote = {move.to_latin() for move in movelist_gote}
    assert actual_sente == set(moves.get(Side.SENTE, ()))
    assert actual_gote == set(moves.get(Side.GOTE, ()))
