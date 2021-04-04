from __future__ import annotations

import re

from enum import IntEnum
from typing import TYPE_CHECKING, Dict, List, Optional, Set

if TYPE_CHECKING:
    from tsumemi.src.shogi.basetypes import Move

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side
from tsumemi.src.shogi.basetypes import HAND_TYPES, KOMA_FROM_SFEN, KOMA_TYPES, SFEN_FROM_KOMA


class Dir(IntEnum):
    # Direction; for use with board representation in Position
    N = -1
    NE = -11
    E = -10
    SE = -9
    S = 1
    SW = 11
    W = 10
    NW = 9


class Position:
    """Represents a shogi position, including board position, side to
    move, and pieces in hand.
    
    Board representation used is mailbox: a 1D array interpreted as a
    9x9 array with padding on the S, E, and W edges. Indices 11-19,
    21-29, ..., 91-99 are the actual board squares, corresponding to
    normal shogi notation.
    """
    def __init__(self) -> None:
        # mailbox representation
        self.board = [Koma.NONE] * 110 # 9x9 with padding on S, E, W edges
        self.reset()
        return
    
    def reset(self) -> None:
        for i in range(110):
            self.board[i] = Koma.NONE
        for i in range(10):
            # place sentinel values
            self.board[i] = Koma.INVALID
            self.board[100+i] = Koma.INVALID
            self.board[i*10] = Koma.INVALID
        # Piece lists/sets
        self.koma_sets: List[Dict[Koma, Set[int]]] = [{koma: set() for koma in KOMA_TYPES} for side in range(2)] # 14 komatypes for each side
        # Hand order is NONE-FU-KY-KE-GI-KI-KA-HI, NONE is unused
        # int is number of copies of piece
        self.hand_sente = [0, 0, 0, 0, 0, 0, 0, 0]
        self.hand_gote = [0, 0, 0, 0, 0, 0, 0, 0]
        self.turn = Side.SENTE
        self.movenum = 1
        return
    
    def __str__(self) -> str:
        rows = []
        for row_num in range(1, 10, 1):
            row = []
            for col_num in range(9, 0, -1):
                row.append(str(self.board[10*col_num + row_num]))
            rows.append("".join(row))
        board = "\n".join(rows)
        elems = [
            board, "NONE-FU-KY-KE-GI-KI-KA-HI",
            "Sente hand:", str(self.hand_sente),
            "Gote hand:", str(self.hand_gote),
            "Turn: Sente" if self.turn == Side.SENTE else "Turn: Gote"
        ]
        return "\n".join(elems)
    
    def set_koma(self, koma: Koma,
            col: Optional[int] = None, row: Optional[int] = None,
            idx: Optional[int] = None
            ) -> None:
        # row and col should be between 1-9 (standard shogi notation)
        if idx is not None:
            self.board[idx] = koma
        elif col is not None and row is not None:
            self.board[col*10 + row] = koma
        return
    
    def get_koma(self, col: Optional[int] = None, row: Optional[int] = None,
            idx: Optional[int] = None
            ) -> Koma:
        if idx is not None:
            return self.board[idx]
        elif col is not None and row is not None:
            return self.board[col*10 + row]
        else:
            return Koma.INVALID
    
    def get_hand(self, side: Side) -> List[int]:
        return self.hand_sente if side is Side.SENTE else self.hand_gote
    
    def set_hand_koma_count(self, side: Side, koma: Koma, count: int) -> None:
        target = self.get_hand(side)
        target[koma] = count
        return
    
    def inc_hand_koma(self, side: Side, ktype: KomaType) -> None:
        target = self.get_hand(side)
        target[ktype] += 1
        return
    
    def dec_hand_koma(self, side: Side, ktype: KomaType) -> None:
        target = self.get_hand(side)
        target[ktype] -= 1
        return
    
    def is_hand_empty(self, side: Side) -> bool:
        target = self.get_hand(side)
        return not any(target)
    
    def make_move(self, move: Move) -> None:
        if move.is_null():
            return
        elif move.is_drop:
            self.dec_hand_koma(move.side, KomaType.get(move.koma))
            self.set_koma(move.koma, idx=move.end_sq)
            self.turn = self.turn.switch()
            self.movenum += 1
            return
        else:
            self.set_koma(Koma.NONE, idx=move.start_sq)
            if move.captured != Koma.NONE:
                self.inc_hand_koma(move.side, KomaType.get(move.captured).unpromote())
            self.set_koma(
                move.koma.promote() if move.is_promotion else move.koma,
                idx=move.end_sq
            )
            self.movenum += 1
            return
    
    def unmake_move(self, move: Move) -> None:
        if move.is_null():
            return
        elif move.is_drop:
            self.set_koma(Koma.NONE, idx=move.end_sq)
            self.inc_hand_koma(move.side, KomaType.get(move.koma))
            self.turn = self.turn.switch()
            self.movenum -= 1
            return
        else:
            if move.captured != Koma.NONE:
                self.dec_hand_koma(move.side, KomaType.get(move.captured).unpromote())
            self.set_koma(move.captured, idx=move.end_sq)
            self.set_koma(move.koma, idx=move.start_sq)
            self.movenum -= 1
            return
    
    def from_sfen(self, sfen: str) -> None:
        """Parse an SFEN string and set up the position it represents.
        """
        board, turn, hands, move_num = sfen.split(" ")
        self.reset()
        self.turn = Side.SENTE if turn == "b" else Side.GOTE
        self.movenum = int(move_num)
        rows = board.split("/")
        for i, row in enumerate(rows):
            col_num = 9
            promo = False
            for ch in row:
                if ch.isdigit():
                    col_num -= int(ch)
                    continue
                elif ch == "+":
                    promo = True
                    continue
                else:
                    koma = KOMA_FROM_SFEN[ch]
                    if promo:
                        koma = koma.promote()
                        promo = False
                    self.set_koma(koma, col=col_num, row=i+1)
                    col_num -= 1
        # Hand
        it_hands = re.findall(r"(\d*)([plnsgbrPLNSGBR])", hands)
        for ch_count, ch in it_hands:
            koma = KOMA_FROM_SFEN[ch]
            ktype = KomaType.get(koma)
            target = self.hand_sente if ch.isupper() else self.hand_gote
            count = int(ch_count) if ch_count else 1
            target[ktype] = count
        return
    
    def to_sfen(self) -> str:
        """Return SFEN string representing the current position.
        """
        sfen = []
        # Start with board
        for row_num in range(1, 10, 1):
            blanks = 0
            row = []
            for col_num in range(9, 0, -1):
                idx = 10*col_num + row_num
                koma = self.board[idx]
                if koma is Koma.NONE:
                    blanks += 1
                else:
                    if blanks != 0:
                        row.append(str(blanks))
                        blanks = 0
                    pc_symbol = SFEN_FROM_KOMA[koma]
                    if koma.is_gote():
                        pc_symbol = pc_symbol.lower()
                    row.append(pc_symbol)
            if blanks != 0:
                row.append(str(blanks))
            sfen.extend(row)
            sfen.append("/")
        sfen.pop(-1) # pop extra "/" char
        # Side to move
        stm = " b " if self.turn is Side.SENTE else " w "
        sfen.append(stm)
        # Hands, sente then gote
        if not any(self.hand_sente) and not any(self.hand_gote):
            sfen.append("-")
        else:
            for pcty in HAND_TYPES:
                count = self.hand_sente[pcty]
                if count > 1:
                    sfen.append(str(count))
                if count != 0:
                    sfen.append(SFEN_FROM_KOMA[Koma(pcty)])
            for pcty in HAND_TYPES:
                count = self.hand_gote[pcty]
                if count > 1:
                    sfen.append(str(count))
                if count != 0:
                    sfen.append(SFEN_FROM_KOMA[Koma(pcty)].lower())
        # Move count
        sfen.append(" " + str(self.movenum))
        return "".join(sfen)