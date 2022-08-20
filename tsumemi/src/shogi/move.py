from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import Koma, KomaType, SFEN_FROM_KOMA, KANJI_NOTATION_FROM_KTYPE
from tsumemi.src.shogi.square import KanjiNumber, Square

if TYPE_CHECKING:
    from typing import Any, List
    from tsumemi.src.shogi.basetypes import GameTermination


class Move:
    """Represents one shogi move. Contains enough information to be
    reversible, i.e. a move can be unmade, given the corresponding
    shogi position as well.
    """
    def __init__(self,
            start_sq: Square = Square.NONE,
            end_sq: Square = Square.NONE,
            is_promotion: bool = False,
            koma: Koma = Koma.NONE,
            captured: Koma = Koma.NONE
        ) -> None:
        self.start_sq = start_sq
        self.end_sq = end_sq
        self.is_promotion = is_promotion
        self.side = koma.side()
        self.koma = koma
        self.captured = captured
        self.is_drop = self.start_sq == Square.HAND
        return

    def __eq__(self, obj: Any) -> bool:
        return (
            isinstance(obj, Move)
            and self.start_sq == obj.start_sq
            and self.end_sq == obj.end_sq
            and self.is_promotion == obj.is_promotion
            and self.side == obj.side
            and self.koma == obj.koma
            and self.captured == obj.captured
            and self.is_drop == obj.is_drop
        )

    def __str__(self) -> str:
        return self.to_text()

    def is_null(self) -> bool:
        return False

    def is_pass(self) -> bool:
        return self.start_sq == self.end_sq

    def to_text(self) -> str:
        """Return easily-parseable string representation of a Move.
        Components are:
        - Char representing piece (uppercase means promoted)
        - int (2 digits) for destination square
        - "+" if a promotion, "=" if not
        - int (2 digits) for origin square (00 if drop from hand)
        """
        # the second part is because Koma.OU == Koma.PROMOTED
        koma = self.koma
        is_promoted_koma = koma.is_promoted()
        komatxt = (
            SFEN_FROM_KOMA[self.koma].upper()
            if is_promoted_koma
            else SFEN_FROM_KOMA[self.koma].lower()
        )
        promotetxt = "+" if self.is_promotion else "="
        start_sq = "00" if self.is_drop else self.start_sq
        return "".join((komatxt, str(self.end_sq), promotetxt, str(start_sq)))

    def to_latin(self) -> str:
        return (
            SFEN_FROM_KOMA[self.koma].upper()
            + ("*" if self.is_drop else "")
            + str(self.end_sq)
            + ("" if self.is_drop else ("(" + str(self.start_sq) + ")"))
            + ("+" if self.is_promotion else "")
        )

    def to_ja_kif(self, is_same: bool = False) -> str:
        """Return KIF format move string.
        """
        end_col, end_row = self.end_sq.get_cr()
        res: List[str] = []
        res.extend(["同　"]
            if is_same
            else [str(end_col), KanjiNumber(end_row).name]
        )
        res.append(KANJI_NOTATION_FROM_KTYPE[KomaType.get(self.koma)])
        res.append("成" if self.is_promotion else "")
        res.extend(["打"] if self.is_drop else ["(", str(self.start_sq), ")"])
        return "".join(res)


class NullMove(Move):
    def __init__(self) -> None:
        Move.__init__(self)
        return

    def is_null(self) -> bool:
        return True


class TerminationMove(Move):
    """Contains information about a game-terminating move (e.g.
    resigns, abort, etc)
    """
    def __init__(self, termination: GameTermination) -> None:
        super().__init__()
        self.end = termination
        return

    def to_text(self) -> str:
        return self.end.name

    def to_latin(self) -> str:
        return self.end.name

    def to_ja_kif(self, is_same: bool = False) -> str:
        return str(self.end.value)
