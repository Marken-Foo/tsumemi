from __future__ import annotations

from enum import Enum, EnumMeta, IntFlag
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class MetaEnum(EnumMeta):
    """Override __contains__() method of enum.EnumMeta for syntactic
    sugar: `if item in Enum: ...`
    """

    def __contains__(cls: Any, item: Any) -> bool:
        try:
            cls(item)
        except ValueError:
            return False
        return True


class Side(IntFlag):
    SENTE = 0
    GOTE = 1
    SHITATE = 0
    UWATE = 1

    def is_sente(self) -> bool:
        return not bool(self)

    def switch(self) -> Side:
        return Side(~self & 0b1)


class KomaType(IntFlag):
    NONE = 0
    FU = 1
    KY = 2
    KE = 3
    GI = 4
    KI = 5
    KA = 6
    HI = 7
    OU = 8
    PROMOTED = 1 << 3
    TO = PROMOTED + FU
    NY = PROMOTED + KY
    NK = PROMOTED + KE
    NG = PROMOTED + GI
    UM = PROMOTED + KA
    RY = PROMOTED + HI

    @classmethod
    def get(cls, koma: Koma) -> KomaType:
        return KomaType(koma & 0b1111)

    def promote(self) -> KomaType:
        if self == KomaType.KI or self == KomaType.NONE:
            return self
        return self | KomaType.PROMOTED

    def unpromote(self) -> KomaType:
        if self == KomaType.OU:
            return self
        return self & ~KomaType.PROMOTED

    def is_promoted(self) -> bool:
        return bool((self & KomaType.PROMOTED) and (self & ~KomaType.OU))

    def to_csa(self) -> str:
        """Return CSA name of the corresponding shogi piece type."""
        # mypy 0.971 thinks Enum.name is Optional[str]
        return " * " if self == KomaType.NONE else self.name  # type: ignore


class Koma(IntFlag):
    """Enum representing shogi pieces. Keys are CSA piece names.
    IntFlag is used to allow integer addition and bitwise operations.
    """

    NONE = 0
    INVALID = -1  # for mailbox sentinel value
    FU = 1
    KY = 2
    KE = 3
    GI = 4
    KI = 5
    KA = 6
    HI = 7
    OU = 8
    PROMOTED = 1 << 3
    TO = PROMOTED + FU
    NY = PROMOTED + KY
    NK = PROMOTED + KE
    NG = PROMOTED + GI
    UM = PROMOTED + KA
    RY = PROMOTED + HI
    GOTE = 1 << 4
    vFU = FU | GOTE
    vKY = KY | GOTE
    vKE = KE | GOTE
    vGI = GI | GOTE
    vKI = KI | GOTE
    vKA = KA | GOTE
    vHI = HI | GOTE
    vOU = OU | GOTE
    vTO = (PROMOTED + FU) | GOTE
    vNY = (PROMOTED + KY) | GOTE
    vNK = (PROMOTED + KE) | GOTE
    vNG = (PROMOTED + GI) | GOTE
    vUM = (PROMOTED + KA) | GOTE
    vRY = (PROMOTED + HI) | GOTE

    @classmethod
    def make(cls, side: Side, ktype: KomaType) -> Koma:
        koma = cls(ktype)
        return koma._sente() if side == Side.SENTE else koma._gote()

    def __str__(self) -> str:
        return self.to_csa()

    def to_csa(self) -> str:
        """Return CSA representation of the corresponding shogi piece."""
        if self == Koma.NONE:
            return " * "
        elif self == Koma.INVALID:
            return "INVALID"
        else:
            side_ch = "-" if (self & Koma.GOTE) else "+"
            # mypy 0.971 thinks Enum.name is Optional[str]
            return "".join((side_ch, (self & ~Koma.GOTE).name))  # type: ignore

    def is_gote(self) -> bool:
        return bool(self & Koma.GOTE)

    def _gote(self) -> Koma:
        return self | Koma.GOTE

    def _sente(self) -> Koma:
        return self & ~Koma.GOTE

    def side(self) -> Side:
        return Side.GOTE if self & Koma.GOTE else Side.SENTE

    def promote(self) -> Koma:
        side = self & Koma.GOTE
        return side | KomaType.get(self).promote()

    def unpromote(self) -> Koma:
        return self & ~Koma.PROMOTED

    def is_promoted(self) -> bool:
        return bool((self & Koma.PROMOTED) and (self & 0b111 & ~Koma.OU))


HAND_TYPES: tuple[
    KomaType, KomaType, KomaType, KomaType, KomaType, KomaType, KomaType
] = (
    KomaType.HI,
    KomaType.KA,
    KomaType.KI,
    KomaType.GI,
    KomaType.KE,
    KomaType.KY,
    KomaType.FU,
)


KOMA_TYPES: set[KomaType] = {
    KomaType.FU,
    KomaType.KY,
    KomaType.KE,
    KomaType.GI,
    KomaType.KI,
    KomaType.KA,
    KomaType.HI,
    KomaType.OU,
    KomaType.TO,
    KomaType.NY,
    KomaType.NK,
    KomaType.NG,
    KomaType.UM,
    KomaType.RY,
}


KTYPE_FROM_KANJI: dict[str, KomaType] = {
    "歩": KomaType.FU,
    "香": KomaType.KY,
    "桂": KomaType.KE,
    "銀": KomaType.GI,
    "金": KomaType.KI,
    "角": KomaType.KA,
    "飛": KomaType.HI,
    "玉": KomaType.OU,
    "王": KomaType.OU,
    "と": KomaType.TO,
    "杏": KomaType.NY,
    "圭": KomaType.NK,
    "全": KomaType.NG,
    "馬": KomaType.UM,
    "龍": KomaType.RY,
    "竜": KomaType.RY,
    "・": KomaType.NONE,
}


KANJI_FROM_KTYPE: dict[KomaType, str] = {
    KomaType.FU: "歩",
    KomaType.KY: "香",
    KomaType.KE: "桂",
    KomaType.GI: "銀",
    KomaType.KI: "金",
    KomaType.KA: "角",
    KomaType.HI: "飛",
    KomaType.OU: "玉",
    KomaType.TO: "と",
    KomaType.NY: "杏",
    KomaType.NK: "圭",
    KomaType.NG: "全",
    KomaType.UM: "馬",
    KomaType.RY: "龍",
    KomaType.NONE: "",
}


KANJI_NOTATION_FROM_KTYPE: dict[KomaType, str] = {
    KomaType.FU: "歩",
    KomaType.KY: "香",
    KomaType.KE: "桂",
    KomaType.GI: "銀",
    KomaType.KI: "金",
    KomaType.KA: "角",
    KomaType.HI: "飛",
    KomaType.OU: "玉",
    KomaType.TO: "と",
    KomaType.NY: "成香",
    KomaType.NK: "成桂",
    KomaType.NG: "成銀",
    KomaType.UM: "馬",
    KomaType.RY: "龍",
    KomaType.NONE: "",
}


SFEN_FROM_KOMA: dict[Koma, str] = {
    Koma.FU: "P",
    Koma.KY: "L",
    Koma.KE: "N",
    Koma.GI: "S",
    Koma.KI: "G",
    Koma.KA: "B",
    Koma.HI: "R",
    Koma.OU: "K",
    Koma.TO: "+P",
    Koma.NY: "+L",
    Koma.NK: "+N",
    Koma.NG: "+S",
    Koma.UM: "+B",
    Koma.RY: "+R",
    Koma.vFU: "p",
    Koma.vKY: "l",
    Koma.vKE: "n",
    Koma.vGI: "s",
    Koma.vKI: "g",
    Koma.vKA: "b",
    Koma.vHI: "r",
    Koma.vOU: "k",
    Koma.vTO: "+p",
    Koma.vNY: "+l",
    Koma.vNK: "+n",
    Koma.vNG: "+s",
    Koma.vUM: "+b",
    Koma.vRY: "+r",
}


KOMA_FROM_SFEN: dict[str, Koma] = {
    "P": Koma.FU,
    "L": Koma.KY,
    "N": Koma.KE,
    "S": Koma.GI,
    "G": Koma.KI,
    "B": Koma.KA,
    "R": Koma.HI,
    "K": Koma.OU,
    "p": Koma.vFU,
    "l": Koma.vKY,
    "n": Koma.vKE,
    "s": Koma.vGI,
    "g": Koma.vKI,
    "b": Koma.vKA,
    "r": Koma.vHI,
    "k": Koma.vOU,
}


class GameTermination(str, Enum, metaclass=MetaEnum):
    ABORT = "中断"
    RESIGN = "投了"
    JISHOGI = "持将棋"
    SENNICHITE = "千日手"
    MATE = "詰み"
    FLAG = "切れ負け"
    ILLEGAL_WIN = "反則勝ち"
    ILLEGAL_LOSS = "反則負け"
    NYUUGYOKU = "入玉勝ち"


CODE_FROM_TERMINATION: dict[GameTermination, int] = {
    term: code for code, term in enumerate(list(GameTermination))
}
