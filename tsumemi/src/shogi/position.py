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
        elems = [
            str(self.board_representation),
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
    
    def get_hand_of_side(self, side: Side) -> HandRepresentation:
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
    
    def create_move(self,
            sq1: Square, 
            sq2: Square,
            is_promotion: bool = False
        ) -> Move:
        """Creates a move from two squares. Move need not necessarily
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
                self.inc_hand_koma(
                    move.side,
                    KomaType.get(move.captured).unpromote()
                )
            self.set_koma(
                move.koma.promote() if move.is_promotion else move.koma,
                move.end_sq
            )
            self.turn = self.turn.switch()
            self.movenum += 1
            return
    
    def unmake_move(self, move: Move) -> None:
        """Unplays/retracts a move from the board.
        """
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
                self.dec_hand_koma(
                    move.side,
                    KomaType.get(move.captured).unpromote()
                )
            self.set_koma(move.captured, move.end_sq)
            self.set_koma(move.koma, move.start_sq)
            self.turn = self.turn.switch()
            self.movenum -= 1
            return
    
    def _set_koma_from_sfen(self,
            ch: str, 
            col_num: int,
            row_num: int,
            promotion_flag: bool
        ) -> None:
        try:
            koma = KOMA_FROM_SFEN[ch]
        except KeyError:
            raise ValueError(f"SFEN contains unknown character '{ch}'")
        sq = Square.from_cr(col_num=col_num, row_num=row_num)
        if promotion_flag:
            koma = koma.promote()
        self.set_koma(koma, sq)
        return
    
    def _parse_sfen_board(self, sfen_board: str) -> None:
        # Parses the part of an SFEN string representing the board.
        rows = sfen_board.split("/")
        if len(rows) != 9:
            raise ValueError("SFEN board has wrong number of rows")
        for i, row in enumerate(rows):
            col_num = 9
            promotion_flag = False
            for ch in row:
                if col_num <= 0:
                    raise ValueError("SFEN row has wrong length")
                if ch.isdigit():
                    if promotion_flag:
                        raise ValueError("Digit cannot follow + in SFEN")
                    col_num -= int(ch)
                    continue
                elif ch == "+":
                    if promotion_flag:
                        raise ValueError("+ cannot follow + in SFEN")
                    promotion_flag = True
                    continue
                else:
                    # This line has the intended side effects
                    self._set_koma_from_sfen(
                        ch, col_num, i+1, promotion_flag
                    )
                    promotion_flag = False
                    col_num -= 1
            else: # for-else loop over row
                if col_num != 0:
                    raise ValueError("SFEN row has wrong length")
                if promotion_flag:
                    raise ValueError("SFEN row cannot end with +")
        return
    
    def _parse_sfen_hands(self, sfen_hands: str) -> None:
        it_hands = re.findall(r"(\d*)([plnsgbrPLNSGBR])", sfen_hands)
        for ch_count, ch in it_hands:
            try:
                koma = KOMA_FROM_SFEN[ch]
            except KeyError:
                raise ValueError(f"SFEN contains unknown character '{ch}'")
            ktype = KomaType.get(koma)
            target_hand = self.hand_sente if ch.isupper() else self.hand_gote
            count = int(ch_count) if ch_count else 1
            target_hand.set_komatype_count(ktype, count)
        return
    
    def from_sfen(self, sfen: str) -> None:
        """Parse an SFEN string and set up the position it represents.
        """
        sfen_board, sfen_turn, sfen_hands, sfen_move_num = sfen.split(" ")
        self.reset()
        if sfen_turn == "b":
            self.turn = Side.SENTE
        elif sfen_turn == "w":
            self.turn = Side.GOTE
        else:
            # This is possibly too strict
            raise ValueError("SFEN contains unknown side to move")
        try:
            self.movenum = int(sfen_move_num)
        except ValueError:
            raise ValueError(
                f"SFEN contains unknown movenumber '{sfen_move_num}'"
            )
        try:
            self._parse_sfen_board(sfen_board)
            self._parse_sfen_hands(sfen_hands)
        except ValueError as e:
            raise ValueError(f"Invalid SFEN: '{sfen}'") from e
        return
    
    def to_sfen(self) -> str:
        """Return SFEN string representing the current position.
        """
        sfen_board = self.board_representation.to_sfen()
        sfen_turn = "b" if self.turn is Side.SENTE else "w"
        if self.hand_sente.is_empty() and self.hand_gote.is_empty():
            sfen_hands = "-"
        else:
            sfen_hands = "".join((
                self.hand_sente.to_sfen(),
                self.hand_gote.to_sfen().lower()
            ))
        sfen_move_num = str(self.movenum)
        return " ".join((sfen_board, sfen_turn, sfen_hands, sfen_move_num))