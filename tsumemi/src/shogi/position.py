from __future__ import annotations

import re

from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Set
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


class BoardRepresentation:
    # Internal representation for the position.
    # Board representation used is mailbox.
    # 1D array interpreted as a 9x9 array with padding.
    # Its interfaces should use Squares.
    def __init__(self) -> None:
        self.board: List[Koma] = [Koma.INVALID] * 143
        # indices of squares containing Koma.NONE (empty squares)
        self.empty_idxs: Set[int] = set()
        self.koma_sets: Dict[Koma, Set[int]] = {}
        self.reset()
        return
    
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


class Position:
    """Represents a shogi position, including board position, side to
    move, and pieces in hand.
    """
    def __init__(self) -> None:
        self.board_representation = BoardRepresentation()
        self.hand_sente = HandRepresentation()
        self.hand_gote = HandRepresentation()
        self.turn = Side.SENTE
        self.movenum = 1
        return
    
    def __str__(self) -> str:
        """Return visual text representation of position.
        """
        rows = []
        for row_num in range(1, 10, 1):
            row = []
            for col_num in range(9, 0, -1):
                row.append(str(self.board_representation.board[self.board_representation.cr_to_idx(col_num, row_num)]))
            rows.append("".join(row))
        board = "\n".join(rows)
        elems = [
            board, "NONE-FU-KY-KE-GI-KI-KA-HI",
            "Sente hand:", str(self.hand_sente),
            "Gote hand:", str(self.hand_gote),
            "Turn: Sente" if self.turn == Side.SENTE else "Turn: Gote"
        ]
        return "\n".join(elems)
    
    def reset(self) -> None:
        self.board_representation.reset()
        self.hand_sente.reset()
        self.hand_gote.reset()
        self.turn = Side.SENTE
        self.movenum = 1
        return
    
    def get_hand_of_side(self, side: Side) -> Dict[KomaType, int]:
        return self.hand_sente if side is Side.SENTE else self.hand_gote
    
    def set_hand_koma_count(self,
            side: Side,
            ktype: KomaType,
            count: int
        ) -> None:
        hand = self.get_hand_of_side(side)
        hand.set_komatype_count(ktype, count)
        return
    
    def inc_hand_koma(self, side: Side, ktype: KomaType) -> None:
        hand = self.get_hand_of_side(side)
        hand.inc_komatype(ktype)
        return
    
    def dec_hand_koma(self, side: Side, ktype: KomaType) -> None:
        hand = self.get_hand_of_side(side)
        hand.dec_komatype(ktype)
        return
    
    def is_hand_empty(self, side: Side) -> bool:
        return self.get_hand_of_side(side).is_empty()
    
    def set_koma(self, koma: Koma, sq: Square) -> None:
        return self.board_representation.set_koma(koma, sq)
    
    def get_koma(self, sq: Square) -> Koma:
        return self.board_representation.get_koma(sq)
    
    def create_move(self, sq1: Square, sq2: Square, is_promotion: bool = False) -> Move:
        """Creates a move from two squares. Move may not necessarily
        be legal or even valid.
        """
        return Move(
            start_sq=sq1,
            end_sq=sq2,
            is_promotion=is_promotion,
            koma=self.get_koma(sq1),
            captured=self.get_koma(sq2)
        )
    
    def make_move(self, move: Move) -> None:
        """Makes a move on the board.
        """
        if move.is_pass():
            # to account for game terminations or other passing moves
            self.movenum += 1
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
            self.turn = self.turn.switch()
            self.movenum += 1
            return
    
    def unmake_move(self, move: Move) -> None:
        """Unplays/retracts a move from the board."""
        if move.is_pass():
            self.movenum -= 1
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
            self.turn = self.turn.switch()
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
            target.set_komatype_count(ktype, count)
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
                koma = self.board_representation.board[self.board_representation.cr_to_idx(col_num, row_num)]
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
        if self.hand_sente.is_empty() and self.hand_gote.is_empty():
            sfen.append("-")
        else:
            for pcty in HAND_TYPES:
                count = self.hand_sente.get_komatype_count(pcty)
                if count > 1:
                    sfen.append(str(count))
                if count != 0:
                    sfen.append(SFEN_FROM_KOMA[Koma(pcty)])
            for pcty in HAND_TYPES:
                count = self.hand_gote.get_komatype_count(pcty)
                if count > 1:
                    sfen.append(str(count))
                if count != 0:
                    sfen.append(SFEN_FROM_KOMA[Koma(pcty)].lower())
        # Move count
        sfen.append(" " + str(self.movenum))
        return "".join(sfen)