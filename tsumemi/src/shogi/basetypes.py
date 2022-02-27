from __future__ import annotations

from enum import Enum, EnumMeta, IntEnum, IntFlag
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict, List, Set, Tuple


class MetaEnum(EnumMeta):
    """Override __contains__() method of enum.EnumMeta for syntactic
    sugar: `if item in Enum: ...`
    """
    def __contains__(self, item) -> bool:
        try:
            self(item)
        except ValueError:
            return False
        return True


class KanjiNumber(IntEnum):
    一 = 1
    二 = 2
    三 = 3
    四 = 4
    五 = 5
    六 = 6
    七 = 7
    八 = 8
    九 = 9
    十 = 10


FULL_WIDTH_NUMBER: Dict[int, str] = {
    0: "０", 1: "１", 2: "２", 3: "３", 4: "４",
    5: "５", 6: "６", 7: "７", 8: "８", 9: "９"
}


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
        return self | KomaType.PROMOTED
    
    def unpromote(self) -> KomaType:
        return self & ~KomaType.PROMOTED
    
    def is_promoted(self) -> bool:
        return bool((self & KomaType.PROMOTED) and (self & ~KomaType.OU))
    
    def to_csa(self) -> str:
        """Return CSA name of the corresponding shogi piece type.
        """
        if self == KomaType.NONE:
            return " * "
        else:
            return self.name


class Koma(IntFlag):
    """Enum representing shogi pieces. Keys are CSA piece names.
    IntFlag is used to allow integer addition and bitwise operations.
    """
    NONE = 0
    INVALID = -1 # for mailbox sentinel value
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
        return koma.sente() if side == Side.SENTE else koma.gote()
    
    def __str__(self) -> str:
        return self.to_csa()
    
    def to_csa(self) -> str:
        """Return CSA representation of the corresponding shogi piece.
        """
        if self == Koma.NONE:
            return " * "
        elif self == Koma.INVALID:
            return "INVALID"
        else:
            side_ch = "-" if (self & Koma.GOTE) else "+"
            return "".join((side_ch, (self & ~Koma.GOTE).name))
    
    def is_gote(self) -> bool:
        return bool(self & Koma.GOTE)
    
    def gote(self) -> Koma:
        return self | Koma.GOTE
    
    def sente(self) -> Koma:
        return self & ~Koma.GOTE
    
    def side(self) -> Side:
        return Side.GOTE if self & Koma.GOTE else Side.SENTE
    
    def promote(self) -> Koma:
        return self | Koma.PROMOTED
    
    def unpromote(self) -> Koma:
        return self & ~Koma.PROMOTED
    
    def is_promoted(self) -> bool:
        return bool((self & Koma.PROMOTED) and (self & ~Koma.OU))


HAND_TYPES: Tuple[
    KomaType, KomaType, KomaType, KomaType,
    KomaType, KomaType, KomaType
    ] = (
    KomaType.HI, KomaType.KA, KomaType.KI, KomaType.GI,
    KomaType.KE, KomaType.KY, KomaType.FU
)


KOMA_TYPES: Set[KomaType] = {
    KomaType.FU, KomaType.KY, KomaType.KE, KomaType.GI,
    KomaType.KI, KomaType.KA, KomaType.HI, KomaType.OU,
    KomaType.TO, KomaType.NY, KomaType.NK, KomaType.NG,
    KomaType.UM, KomaType.RY
}


KTYPE_FROM_KANJI: Dict[str, KomaType] = {
    "歩": KomaType.FU, "香": KomaType.KY, "桂": KomaType.KE, "銀": KomaType.GI,
    "金": KomaType.KI, "角": KomaType.KA, "飛": KomaType.HI,
    "玉": KomaType.OU, "王": KomaType.OU,
    "と": KomaType.TO, "杏": KomaType.NY, "圭": KomaType.NK, "全": KomaType.NG,
    "馬": KomaType.UM, "龍": KomaType.RY, "竜": KomaType.RY,
    "・": KomaType.NONE
}


KANJI_FROM_KTYPE: Dict[KomaType, str] = {
    KomaType.FU: "歩", KomaType.KY: "香", KomaType.KE: "桂", KomaType.GI: "銀",
    KomaType.KI: "金", KomaType.KA: "角", KomaType.HI: "飛", KomaType.OU: "玉",
    KomaType.TO: "と", KomaType.NY: "杏", KomaType.NK: "圭", KomaType.NG: "全",
    KomaType.UM: "馬", KomaType.RY: "龍",
    KomaType.NONE: ""
}


KANJI_NOTATION_FROM_KTYPE: Dict[KomaType, str] = {
    KomaType.FU: "歩", KomaType.KY: "香", KomaType.KE: "桂", KomaType.GI: "銀",
    KomaType.KI: "金", KomaType.KA: "角", KomaType.HI: "飛", KomaType.OU: "玉",
    KomaType.TO: "と", KomaType.NY: "成香", KomaType.NK: "成桂", KomaType.NG: "成銀",
    KomaType.UM: "馬", KomaType.RY: "龍",
    KomaType.NONE: ""
}


SFEN_FROM_KOMA: Dict[Koma, str] = {
    Koma.FU: "P", Koma.KY: "L", Koma.KE: "N", Koma.GI: "S",
    Koma.KI: "G", Koma.KA: "B", Koma.HI: "R", Koma.OU: "K",
    Koma.TO: "+P", Koma.NY: "+L", Koma.NK: "+N", Koma.NG: "+S",
    Koma.UM: "+B", Koma.RY: "+R",
    Koma.vFU: "p", Koma.vKY: "l", Koma.vKE: "n", Koma.vGI: "s",
    Koma.vKI: "g", Koma.vKA: "b", Koma.vHI: "r", Koma.vOU: "k",
    Koma.vTO: "+p", Koma.vNY: "+l", Koma.vNK: "+n", Koma.vNG: "+s",
    Koma.vUM: "+b", Koma.vRY: "+r"
}


KOMA_FROM_SFEN: Dict[str, Koma] = {
    "P": Koma.FU, "L": Koma.KY, "N": Koma.KE, "S": Koma.GI,
    "G": Koma.KI, "B": Koma.KA, "R": Koma.HI, "K": Koma.OU,
    "p": Koma.vFU, "l": Koma.vKY, "n": Koma.vKE, "s": Koma.vGI,
    "g": Koma.vKI, "b": Koma.vKA, "r": Koma.vHI, "k": Koma.vOU
}


class GameTermination(str, Enum, metaclass=MetaEnum):
    ABORT = "中断",
    RESIGN = "投了",
    JISHOGI = "持将棋",
    SENNICHITE = "千日手",
    MATE = "詰み",
    FLAG = "切れ負け",
    ILLEGAL_WIN = "反則勝ち",
    ILLEGAL_LOSS = "反則負け",
    NYUUGYOKU = "入玉勝ち"


CODE_FROM_TERMINATION: Dict[GameTermination, int] = {
    term: code for code, term in enumerate(list(GameTermination))
}


class Square(IntEnum):
    """Represents a square on the shogi board, or a piecetype in hand.
    """
    NONE = 0
    HAND = 82
    b11, b12, b13, b14, b15, b16, b17, b18, b19 = range(1, 10)
    b21, b22, b23, b24, b25, b26, b27, b28, b29 = range(10, 19)
    b31, b32, b33, b34, b35, b36, b37, b38, b39 = range(19, 28)
    b41, b42, b43, b44, b45, b46, b47, b48, b49 = range(28, 37)
    b51, b52, b53, b54, b55, b56, b57, b58, b59 = range(37, 46)
    b61, b62, b63, b64, b65, b66, b67, b68, b69 = range(46, 55)
    b71, b72, b73, b74, b75, b76, b77, b78, b79 = range(55, 64)
    b81, b82, b83, b84, b85, b86, b87, b88, b89 = range(64, 73)
    b91, b92, b93, b94, b95, b96, b97, b98, b99 = range(73, 82)
    
    def __str__(self) -> str:
        col, row = self.get_cr()
        return str(10*col+row)
    
    @classmethod
    def from_cr(cls, col_num: int, row_num: int) -> Square:
        return cls(9*col_num-9+row_num)
    
    @classmethod
    def from_coord(cls, coord: int) -> Square:
        return cls.from_cr(col_num=int(coord/10), row_num=coord%10)
    
    def get_cr(self) -> Tuple[int, int]:
        col = (self-1)// 9 + 1
        row = (self-1) % 9 + 1
        return col, row
    
    def is_board(self) -> bool:
        return self.name.startswith("b")
    
    def is_hand(self) -> bool:
        return self == 82
    
    def is_left_of(self, sq_other: Square, side: Side) -> bool:
        col_diff, _ = self._subtract_squares(sq_other)
        return col_diff > 0 if side.is_sente() else col_diff < 0
    
    def is_right_of(self, sq_other: Square, side: Side) -> bool:
        return sq_other.is_left_of(self, side)
    
    def is_forward_of(self, sq_other: Square, side: Side) -> bool:
        _, row_diff = self._subtract_squares(sq_other)
        return row_diff < 0 if side.is_sente() else row_diff > 0
    
    def is_backward_of(self, sq_other: Square, side: Side) -> bool:
        return sq_other.is_forward_of(self, side)
    
    def is_same_row(self, sq_other: Square) -> bool:
        _, row_diff = self._subtract_squares(sq_other)
        return row_diff == 0
    
    def _subtract_squares(self, sq_other: Square) -> Tuple[int, int]:
        col, row = self.get_cr()
        col_other, row_other = sq_other.get_cr()
        return (col - col_other, row - row_other)
    
    def is_immediately_forward_of(self, sq_other: Square, side: Side) -> bool:
        forward = -1 if side.is_sente() else 1
        return self._subtract_squares(sq_other) == (0, forward)
    
    def to_japanese(self) -> str:
        col, row = self.get_cr()
        return FULL_WIDTH_NUMBER[col] + KanjiNumber(row).name


class Move:
    """Represents one shogi move. Contains enough information to be
    reversible, i.e. a move can be unmade, given the corresponding
    shogi position as well.
    """
    def __init__(self,
            start_sq: Square = Square.NONE,
            end_sq: Square = Square.NONE,
            is_promotion: bool = False,
            koma: Koma = Koma.NONE, captured: Koma = Koma.NONE
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