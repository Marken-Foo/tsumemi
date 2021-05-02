from __future__ import annotations

import re

from enum import IntEnum
from typing import TYPE_CHECKING, Dict, List, Set, Tuple

if TYPE_CHECKING:
    from tsumemi.src.shogi.basetypes import Move

from tsumemi.src.shogi.basetypes import Koma, KomaType, Side, Square
from tsumemi.src.shogi.basetypes import HAND_TYPES, KOMA_FROM_SFEN, KOMA_TYPES, SFEN_FROM_KOMA


class Dir(IntEnum):
    # Direction; for use with board representation in Position
    N = -1
    NE = -14
    E = -13
    SE = -12
    S = 1
    SW = 14
    W = 13
    NW = 12


class Position:
    """Represents a shogi position, including board position, side to
    move, and pieces in hand.
    
    Board representation used is mailbox: a 1D array interpreted as a
    9x9 array with padding.
    """
    def __init__(self) -> None:
        # mailbox representation
        self.board = [Koma.NONE] * 143 # 11 columns, 13 rows
        self.reset()
        return
    
    def reset(self) -> None:
        for i in range(143):
            self.board[i] = Koma.INVALID
        for col_num in range(1, 10):
            for row_num in range(1, 10):
                self.board[self.cr_to_idx(col_num, row_num)] = Koma.NONE
        # Koma set; indexed by side and komatype, contents are indices of where they are located on the board.
        koma_sente: Dict[Koma, Set[int]] = {Koma.make(Side.SENTE, ktype): set() for ktype in KOMA_TYPES}
        koma_gote: Dict[Koma, Set[int]] = {Koma.make(Side.GOTE, ktype): set() for ktype in KOMA_TYPES}
        self.koma_sets: Dict[Koma, Set[int]] = {**koma_sente, **koma_gote}
        # Hand order is NONE-FU-KY-KE-GI-KI-KA-HI, NONE is unused
        # int is number of copies of piece
        self.hand_sente = [0, 0, 0, 0, 0, 0, 0, 0]
        self.hand_gote = [0, 0, 0, 0, 0, 0, 0, 0]
        self.turn = Side.SENTE
        self.movenum = 1
        return
    
    def sq_to_idx(self, sq: Square) -> int:
        # Everything that comes from a Square should go through this
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
    
    def __str__(self) -> str:
        """Return visual text representation of position.
        """
        rows = []
        for row_num in range(1, 10, 1):
            row = []
            for col_num in range(9, 0, -1):
                row.append(str(self.board[self.cr_to_idx(col_num, row_num)]))
            rows.append("".join(row))
        board = "\n".join(rows)
        elems = [
            board, "NONE-FU-KY-KE-GI-KI-KA-HI",
            "Sente hand:", str(self.hand_sente),
            "Gote hand:", str(self.hand_gote),
            "Turn: Sente" if self.turn == Side.SENTE else "Turn: Gote"
        ]
        return "\n".join(elems)
    
    def set_koma(self, koma: Koma, sq: Square) -> None:
        prev_koma = self.get_koma(sq)
        self.board[self.sq_to_idx(sq)] = koma
        if koma != Koma.NONE and koma != Koma.INVALID:
            self.koma_sets[koma].add(self.sq_to_idx(sq))
        if prev_koma != Koma.NONE and prev_koma != Koma.INVALID:
            self.koma_sets[prev_koma].discard(self.sq_to_idx(sq))
        return
    
    def get_koma(self, sq: Square) -> Koma:
        return self.board[self.sq_to_idx(sq)]
    
    def get_hand(self, side: Side) -> List[int]:
        return self.hand_sente if side is Side.SENTE else self.hand_gote
    
    def set_hand_koma_count(self, side: Side, ktype: KomaType, count: int) -> None:
        target = self.get_hand(side)
        target[ktype] = count
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
    
    def create_move(self, sq1: Square, sq2: Square, is_promotion: bool = False) -> Move:
        """Creates a move from two squares. Move may not necessarily
        be legal or even valid.
        """
        return Move(start_sq=sq1, end_sq=sq2, is_promotion=is_promotion,
            koma=self.get_koma(sq1), captured=self.get_koma(sq2)
        )
    
    def make_move(self, move: Move) -> None:
        """Makes a move on the board.
        """
        if move.is_null():
            return
        elif move.is_drop:
            self.dec_hand_koma(move.side, KomaType.get(move.koma))
            self.set_koma(move.koma, move.end_sq)
            self.turn = self.turn.switch()
            self.movenum += 1
            return
        else:
            self.set_koma(Koma.NONE, move.start_sq)
            if move.captured != Koma.NONE:
                self.inc_hand_koma(move.side, KomaType.get(move.captured).unpromote())
            self.set_koma(
                move.koma.promote() if move.is_promotion else move.koma,
                move.end_sq
            )
            self.movenum += 1
            return
    
    def unmake_move(self, move: Move) -> None:
        """Unplays/retracts a move from the board."""
        if move.is_null():
            return
        elif move.is_drop:
            self.set_koma(Koma.NONE, move.end_sq)
            self.inc_hand_koma(move.side, KomaType.get(move.koma))
            self.turn = self.turn.switch()
            self.movenum -= 1
            return
        else:
            if move.captured != Koma.NONE:
                self.dec_hand_koma(move.side, KomaType.get(move.captured).unpromote())
            self.set_koma(move.captured, move.end_sq)
            self.set_koma(move.koma, move.start_sq)
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
                    self.set_koma(koma, Square.from_cr(col_num=col_num, row_num=i+1))
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
                koma = self.board[self.cr_to_idx(col_num, row_num)]
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