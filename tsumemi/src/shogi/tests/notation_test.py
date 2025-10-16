from __future__ import annotations
import itertools

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KOMA_FROM_SFEN
from tsumemi.src.shogi.square import Square

if TYPE_CHECKING:
    from collections.abc import Sequence
    from tsumemi.src.shogi.basetypes import Koma


def read_notation_test_file(filename: str) -> list[NotationTestCase]:
    """
    Assumes test file consists of test cases, each separated by a newline.
    Each test case consists of 4 lines:

    - The name of the test.
    - A comma-separated list of koma positions in the format `[1-9][1-9](SFEN koma)`, e.g. `53+P, 64s, 19+l`. Whitespace around the commas is allowed.
    - The start square, end square, and whether the move is a promotion (`+` if promotion, `=` if not), separated by spaces. e.g. `83 84 =`
    - The expected move string, e.g. `S36-35` or `４三と引`
    """
    with open(filename, encoding="utf-8") as test_file:
        return [
            _read_notation_test_case(
                test_name=test_name.strip(),
                koma_locations=koma_locations.strip(),
                move_params=move_params.strip(),
                expected_move_string=expected_move_string.strip(),
            )
            for (
                test_name,
                koma_locations,
                move_params,
                expected_move_string,
                _,
            ) in itertools.zip_longest(*[test_file] * 5)
        ]


def _read_notation_test_case(
    test_name: str, koma_locations: str, move_params: str, expected_move_string: str
) -> NotationTestCase:
    """
    Reads a single test case. Refer to documentation for `_read_notation_test_file` for the format.
    """
    start_coord, end_coord, promotion = move_params.split(" ")
    if promotion == "+":
        is_promotion = True
    elif promotion == "=":
        is_promotion = False
    else:
        raise ValueError("Unknown promotion value (must be '+' or '=')")
    return NotationTestCase(
        test_name,
        _parse_koma_location_list(koma_locations),
        start_sq=_parse_square(start_coord),
        end_sq=_parse_square(end_coord),
        is_promotion=is_promotion,
        expected=expected_move_string,
    )


def _parse_koma_location_list(input: str) -> list[tuple[Square, Koma]]:
    """
    Assumes input is a comma-separated list of square and koma, e.g. "32S,11l,12k,23+P".
    """
    koma_locations = (s.strip() for s in input.strip().split(","))
    return [(_parse_square(s[0:2]), _parse_koma(s[2:])) for s in koma_locations]


def _parse_koma(input: str) -> Koma:
    """
    Assumes input is a valid SFEN koma string, e.g. "L", "k", "+P", or "+s".
    - Either one character, or two characters with the first being "+"
    - The non-"+" character must be a valid koma in SFEN
    - The "+" prefix indicates a promoted piece
    - Uppercase input indicates sente, lowercase indicates gote
    """
    if input.startswith("+"):
        return KOMA_FROM_SFEN[input[1:]].promote()
    else:
        return KOMA_FROM_SFEN[input]


def _parse_square(input: str) -> Square:
    """
    Assumes input is a two-digit number without zeroes, i.e. matching the regex `[1-9][1-9]`.
    First number represents the column, second represents row.
    """
    return Square.from_coord(int(input))


class NotationTestCase:
    def __init__(
        self,
        name: str,
        koma_locations: list[tuple[Square, Koma]],
        start_sq: Square,
        end_sq: Square,
        is_promotion: bool,
        expected: str,
    ) -> None:
        self.name = name
        self.koma_locations = koma_locations
        self.start_sq = start_sq
        self.end_sq = end_sq
        self.is_promotion = is_promotion
        self.expected = expected


def get_parametrization_from_test_cases(
    test_cases: list[NotationTestCase],
) -> tuple[list[Sequence[object] | object], list[str]]:
    argvalues: list[Sequence[object] | object] = []
    names: list[str] = []
    for t in test_cases:
        argvalues.append(
            (t.koma_locations, t.start_sq, t.end_sq, t.is_promotion, t.expected)
        )
        names.append(t.name)
    return (argvalues, names)
