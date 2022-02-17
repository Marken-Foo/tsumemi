from __future__ import annotations

from enum import IntEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Set
    from tsumemi.src.shogi.basetypes import KomaType

from tsumemi.src.shogi.basetypes import Koma, Side, Square
from tsumemi.src.shogi.basetypes import HAND_TYPES, KOMA_TYPES, SFEN_FROM_KOMA


class Dir(IntEnum):
    # Direction; dependent on board representation
    N = -1
    NE = -14
    E = -13
    SE = -12
    S = 1
    SW = 14
    W = 13
    NW = 12


class BoardRepresentation:
    # Internal representation for the position.
    # Board representation used is mailbox.
    # 1D array interpreted as a 9x9 array with padding.
    def __init__(self) -> None:
        self.board: List[Koma] = [Koma.INVALID] * 143
        # indices of squares containing Koma.NONE (empty squares)
        self.empty_idxs: Set[int] = set()
        self.koma_sets: Dict[Koma, Set[int]] = {}
        self.reset()
        return
    
    def __str__(self) -> str:
        rows = []
        for row_num in range(1, 10, 1):
            row = []
            for col_num in range(9, 0, -1):
                koma = self.board[self.cr_to_idx(col_num, row_num)]
                row.append(str(koma))
            rows.append("".join(row))
        board = "\n".join(rows)
        return board
    
    def to_sfen(self) -> str:
        board = []
        for row_num in range(1, 10):
            board.append(self._build_sfen_row(row_num))
        return "/".join(board)
    
    def _build_sfen_row(self, row_num: int) -> str:
        blanks = 0
        row: List[str] = []
        for col_num in range(9, 0, -1):
            koma = self.board[self.cr_to_idx(col_num, row_num)]
            if koma is Koma.NONE:
                blanks += 1
                continue
            elif blanks != 0:
                row.append(str(blanks))
                blanks = 0
            koma_symbol = SFEN_FROM_KOMA[koma]
            if koma.is_gote():
                koma_symbol = koma_symbol.lower()
            row.append(koma_symbol)
        if blanks != 0:
            row.append(str(blanks))
        return "".join(row)
    
    def reset(self) -> None:
        for i in range(143):
            self.board[i] = Koma.INVALID
        for col_num in range(1, 10):
            for row_num in range(1, 10):
                idx = self.cr_to_idx(col_num, row_num)
                self.board[idx] = Koma.NONE
                self.empty_idxs.add(idx)
        # Koma set: indexed by side and komatype
        # contents are indices of where they are located on the board.
        koma_sente: Dict[Koma, Set[int]] = {
            Koma.make(Side.SENTE, ktype): set() for ktype in KOMA_TYPES
        }
        koma_gote: Dict[Koma, Set[int]] = {
            Koma.make(Side.GOTE, ktype): set() for ktype in KOMA_TYPES
        }
        self.koma_sets = {
            **koma_sente, **koma_gote
        }
        return
    
    def sq_to_idx(self, sq: Square) -> int:
        return self.cr_to_idx(*(sq.get_cr()))
    
    def idx_to_sq(self, idx: int) -> Square:
        col = self.idx_to_c(idx)
        row = self.idx_to_r(idx)
        return Square.from_cr(col, row)
    
    def cr_to_idx(self, col_num: int, row_num: int) -> int:
        return 13*col_num + row_num+1
    
    def idx_to_c(self, idx: int) -> int:
        return (idx-1) // 13
    
    def idx_to_r(self, idx: int) -> int:
        return (idx-1) % 13
    
    def is_idx_in_zone(self, idx: int, side: Side) -> bool:
        row = self.idx_to_r(idx)
        if side == Side.SENTE:
            return True if row in (1, 2, 3) else False
        else:
            return True if row in (7, 8, 9) else False
    
    def set_koma(self, koma: Koma, sq: Square) -> None:
        prev_koma = self.get_koma(sq)
        idx = self.sq_to_idx(sq)
        self.board[idx] = koma
        if prev_koma == Koma.INVALID:
            raise ValueError(
                f"Cannot set koma {str(koma)} to replace Koma.INVALID"
            )
        if koma == Koma.INVALID:
            raise ValueError(
                f"Cannot set koma to be Koma.INVALID"
            )
        if koma == Koma.NONE:
            self.empty_idxs.add(idx)
        else:
            self.koma_sets[koma].add(idx)
            self.empty_idxs.discard(idx)
        if prev_koma != Koma.NONE:
            self.koma_sets[prev_koma].discard(idx)
        return
    
    def get_koma(self, sq: Square) -> Koma:
        return self.board[self.sq_to_idx(sq)]


class HandRepresentation:
    def __init__(self) -> None:
        self.mochigoma_dict: Dict[KomaType, int] = {
            ktype: 0 for ktype in HAND_TYPES
        }
        return
    
    def __str__(self) -> str:
        string_gen = (
            f"{str(ktype)}: {str(count)}"
            for ktype, count in self.mochigoma_dict.items()
        )
        return ", ".join(string_gen)
    
    def to_sfen(self) -> str:
        if self.is_empty():
            # Writing '-' in SFEN needs both hands, not just one
            return ""
        sfen_hand = []
        for ktype in HAND_TYPES:
            count = self.mochigoma_dict[ktype]
            if count > 1:
                sfen_hand.append(str(count))
            if count > 0:
                sfen_hand.append(SFEN_FROM_KOMA[Koma(ktype)])
        return "".join(sfen_hand)
    
    def reset(self) -> None:
        self.mochigoma_dict = {
            ktype: 0 for ktype in HAND_TYPES
        }
        return
    
    def set_komatype_count(self, ktype: KomaType, count: int) -> None:
        self.mochigoma_dict[ktype] = count
        return
    
    def get_komatype_count(self, ktype: KomaType) -> int:
        return self.mochigoma_dict[ktype]
    
    def inc_komatype(self, ktype: KomaType) -> None:
        try:
            self.mochigoma_dict[ktype] += 1
        except KeyError:
            self.mochigoma_dict[ktype] = 1
        return
    
    def dec_komatype(self, ktype: KomaType) -> None:
        if self.mochigoma_dict[ktype] <= 0:
            raise ValueError("Cannot decrease number of pieces in hand below 0")
        self.mochigoma_dict[ktype] -= 1
        return
    
    def is_empty(self) -> bool:
        return not any(self.mochigoma_dict.values())
