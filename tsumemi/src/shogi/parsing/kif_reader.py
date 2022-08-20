from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tsumemi.src.shogi.parsing.base_readers_visitors import ParserVisitor, Reader
from tsumemi.src.shogi.basetypes import GameTermination, Koma
from tsumemi.src.shogi.basetypes import Side
from tsumemi.src.shogi.basetypes import HAND_TYPES, KTYPE_FROM_KANJI
from tsumemi.src.shogi.game import Game
from tsumemi.src.shogi.move import Move, TerminationMove
from tsumemi.src.shogi.square import KanjiNumber, Square

if TYPE_CHECKING:
    import typing
    from typing import Dict, Generator, List, Sequence, Tuple
    from tsumemi.src.shogi.basetypes import KomaType


# May be common to other formats than just KIF
SFEN_FROM_HANDICAP: Dict[str, str] = {
    "平手": "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
    "香落ち": "lnsgkgsn1/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "右香落ち": "1nsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "角落ち": "lnsgkgsnl/1r7/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "飛車落ち": "lnsgkgsnl/7b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "飛香落ち": "lnsgkgsn1/7b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "二枚落ち": "lnsgkgsnl/9/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "三枚落ち": "1nsgkgsnl/9/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "四枚落ち": "1nsgkgsn1/9/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "五枚落ち": "2sgkgsn1/9/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "左五枚落ち": "1nsgkgs2/9/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "六枚落ち": "2sgkgs2/9/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "八枚落ち": "3gkg3/9/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    "十枚落ち": "4k4/9/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
}


KIF_MOVELINE_REGEX: re.Pattern = re.compile(
    r"(?P<movenum>\d*)"
    r"\s*"
    r"(?P<move>[　\S]+)"
    r"\s*"
    r"(?:\(\s*"
    r"(?P<movetime>\d+:\d{2})"
    r"\s*/\s*"
    r"(?P<totaltime>\d+:\d{2}:\d{2})"
    r"\s*\))?"
)


KIF_MOVE_REGEX: re.Pattern = re.compile(
    r"(?P<sq_dest>(?:(?:同　)|(?:\d[一二三四五六七八九])))"
    r"(?P<koma>成?[歩香桂銀金角飛玉と龍竜馬全圭杏])"
    r"(?P<drop_prom>[打成])?"
    r"(?:\((?P<sq_origin>\d{2})\))?"
)


KIF_VARIATION_REGEX: re.Pattern = re.compile(
    r"変化：(?P<movenum>\d+)手"
)


class KifReader(Reader):
    def __init__(self) -> None:
        super().__init__()
        return

    def read(self, handle: typing.TextIO, visitor: ParserVisitor) -> Game:
        self.game.reset()
        line = handle.readline()
        while line != "":
            line = line.lstrip().rstrip()
            if line == "":
                pass
            elif line.startswith("手合割："):
                handicap_sfen = self.read_handicap_line(line)
                visitor.visit_handicap(self, handicap_sfen)
            elif line.startswith("後手の持駒："):
                # Signals start of BOD, read all of it
                bod_lines = [line]
                while (not line.startswith("先手の持駒：")) and line:
                    line = handle.readline()
                    bod_lines.append(line.lstrip().rstrip())
                self.read_bod(bod_lines)
                #visitor.visit_board(self, bod_lines)
            elif line.startswith("手数--"):
                # movesection delineation
                pass
            elif line[0].isdigit():
                # Signals a move; thus, requires moves to be numbered.
                move = self.read_move(line)
                visitor.visit_move(self, move)
            elif line.startswith("*"):
                visitor.visit_comment(self, line)
            elif line.startswith("#"):
                visitor.visit_escape(self, line)
            elif line.startswith("変化："):
                # Variation
                self.read_variation(line)
                # visitor.visit_variation(self, line)
            else:
                # Unknown line; skip it
                pass
            # MUST fallthrough to here to complete one while iteration
            line = handle.readline()
        self.game.go_to_start()
        return self.game

    def read_handicap_line(self, line: str) -> str:
        """Reads the handicap field. Returns a SFEN string.
        """
        val = line.split("：")[1]
        try:
            return SFEN_FROM_HANDICAP[val]
        except KeyError as exc:
            raise KeyError("Unknown handicap: " + val) from exc

    def read_bod(self, lines: Sequence[str]) -> None:
        """Read the BOD representation given by the argument lines,
        and set reader's board accordingly.

        lines should be a list of exactly 14 strings as per BOD:
        gote's hand, decorative coordinates, decorative line,
        9x board rows, decorative line, sente's hand.
        """
        pos = self.game.position
        movetree = self.game.movetree
        line_gote_hand = lines[0]
        line_sente_hand = lines[-1]
        lines_board = lines[3:-2] # This should be exactly 9 strings
        # Hands
        for ktype, count in _read_bod_hand(line_gote_hand):
            pos.set_hand_koma_count(Side.GOTE, ktype, count)
        for ktype, count in _read_bod_hand(line_sente_hand):
            pos.set_hand_koma_count(Side.SENTE, ktype, count)
        # Board
        for row_idx, line_rank in enumerate(lines_board):
            for col_idx, koma in enumerate(_read_bod_row(line_rank)):
                pos.set_koma(
                    koma, Square.from_cr(col_num=9-col_idx, row_num=row_idx+1)
                )
        movetree.start_pos = pos.to_sfen()
        return

    def read_move(self, line: str) -> Move:
        game = self.game
        movenum, movestr, _, _ = _read_kif_move_line(line)
        # Identify move components
        if movestr in GameTermination:
            return TerminationMove(GameTermination(movestr))
        dest_str, koma_str, drop_prom, sq_origin = _read_kif_move(movestr)
        prev_end_sq = (
            Square.NONE if game.curr_node.move.is_null()
            else game.curr_node.move.end_sq
        )
        end_sq = _read_kif_dest_sq(dest_str, prev_end_sq)
        captured = game.position.get_koma(end_sq)
        ktype = _read_kif_komatype(koma_str)
        is_drop = (drop_prom == "打")
        if is_drop and ktype not in HAND_TYPES:
            raise ValueError("Koma " + str(ktype) + " cannot be dropped")
        start_sq = _read_kif_origin_sq(sq_origin, is_drop)
        is_promotion = (drop_prom == "成")
        # Construct Move
        side = Side.SENTE if (movenum % 2 == 1) else Side.GOTE
        koma = Koma.make(side, ktype)
        return Move(start_sq, end_sq, is_promotion, koma, captured)

    def read_variation(self, line: str) -> None:
        game = self.game
        line_match = re.match(KIF_VARIATION_REGEX, line)
        if line_match is None:
            raise ValueError("KIF variation regex failed to match: " + line)
        var_movenum = int(line_match.group("movenum"))
        while (
            (not game.curr_node.is_null())
            and game.curr_node.movenum != var_movenum
        ):
            game.go_prev_move()
        game.go_prev_move() # Once more to reach the prior move
        if game.curr_node.is_null():
            raise Exception("HALP desired movenum not found")
        return


def _read_bod_hand(bod_hand_line: str) -> List[Tuple[KomaType, int]]:
    # Reads a line representing a player's hand in BOD format
    # Returns a list of (koma type, piece count).
    res = []
    hand_str = bod_hand_line.split("：")[1]
    hand = re.split("　| ", hand_str)
    for entry in hand:
        if entry == "なし":
            break
        ktype = KTYPE_FROM_KANJI[entry[0]]
        if len(entry) == 1:
            count = 1
        elif len(entry) == 2:
            count = int(KanjiNumber[entry[1]])
        elif len(entry) == 3:
            # e.g. 十八 = 18; max for a shogi position should be 18 (pawns)
            count = int(KanjiNumber[entry[1]]) + int(KanjiNumber[entry[2]])
        res.append((ktype, count))
    return res


def _read_bod_row(bod_board_line: str
    ) -> Generator[Koma, None, None]:
    # Reads a line representing a row of the boarda in BOD format.
    # Returns a generator of Koma.
    rank_str = bod_board_line.split("|")[1]
    piece_strs = (rank_str[i:i+2] for i in range(0, len(rank_str), 2))
    return (
        Koma.make(
            Side.GOTE if piece_str[0] == "v" else Side.SENTE,
            KTYPE_FROM_KANJI[piece_str[1]]
        )
        for piece_str in piece_strs
    )


def _read_kif_move_line(line: str) -> Tuple[int, str, str, str]:
    line_match = re.search(KIF_MOVELINE_REGEX, line)
    if line_match is None:
        raise TypeError("Match object is None, cannot identify move from line:\n" + line)
    move_num = line_match.group("movenum")
    move_str = line_match.group("move")
    move_time = line_match.group("movetime")
    total_time = line_match.group("totaltime")
    return int(move_num), move_str, move_time, total_time


def _read_kif_move(move_str: str) -> Tuple[str, str, str, str]:
    move_match = re.search(KIF_MOVE_REGEX, move_str)
    if move_match is None:
        raise ValueError("KIF move regex failed to match movestr: " + move_str)
    dest_str = move_match.group("sq_dest")
    koma_str = move_match.group("koma")
    drop_prom_str = move_match.group("drop_prom")
    sq_origin_str = move_match.group("sq_origin")
    return dest_str, koma_str, drop_prom_str, sq_origin_str


def _read_kif_dest_sq(dest_str: str, sq_prev: Square) -> Square:
    if dest_str == "同　":
        if sq_prev == Square.NONE:
            raise ValueError("No last move specified for same destination quare.")
        return sq_prev
    col = int(dest_str[0])
    row = int(KanjiNumber[dest_str[1]])
    return Square.from_cr(col, row)


def _read_kif_komatype(koma_str: str) -> KomaType:
    try:
        return (
            KTYPE_FROM_KANJI[koma_str[1]].promote()
            if koma_str[0] == "成"
            else KTYPE_FROM_KANJI[koma_str]
        )
    except KeyError as exc:
        raise KeyError("Unknown koma: " + koma_str) from exc


def _read_kif_origin_sq(sq_origin_str: str, is_drop: bool) -> Square:
    return (
        Square.HAND if is_drop
        else Square.from_coord(int(sq_origin_str))
    )
