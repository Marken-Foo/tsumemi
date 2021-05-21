from __future__ import annotations

import re
import typing

from enum import IntEnum
from typing import TYPE_CHECKING, Dict, Sequence

from tsumemi.src.shogi.basetypes import GameTermination, KanjiNumber, Koma, Move, Side, Square, TerminationMove
from tsumemi.src.shogi.basetypes import HAND_TYPES, KTYPE_FROM_KANJI
from tsumemi.src.shogi.game import Game

if TYPE_CHECKING:
    from tsumemi.src.shogi.basetypes import KomaType


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


class ParserVisitor:
    # the idea is that a kif_reader/sfen_reader/csa_reader can accept
    # the same visitor, which holds diff methods for diff readers.
    def __init__(self) -> None:
        return
    
    def visit_board(self, reader: Reader, lines: Sequence[str]) -> None:
        pass
    
    def visit_comment(self, reader: Reader, line: str) -> None:
        pass
    
    def visit_escape(self, reader: Reader, line: str) -> None:
        pass
    
    def visit_handicap(self, reader: Reader, line: str) -> None:
        pass
    
    def visit_move(self, reader: Reader, line: str) -> None:
        pass
    
    def visit_variation(self, reader: Reader, line: str) -> None:
        pass


class GameBuilderPVis(ParserVisitor):
    def __init__(self) -> None:
        return
    
    def visit_board(self, reader: Reader, lines: Sequence[str]) -> None:
        """Read the BOD representation given by the argument lines,
        and set reader's board accordingly.
        
        lines should be a list of exactly 14 strings as per BOD:
        gote's hand, decorative coordinates, decorative line,
        9x board rows, decorative line, sente's hand.
        """
        pos = reader.game.position
        movetree = reader.game.movetree
        line_gote_hand = lines[0]
        line_sente_hand = lines[-1]
        # Hands
        def read_hand(line):
            res = []
            hand_str = line.split("：")[1]
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
        for ktype, count in read_hand(line_gote_hand):
            pos.set_hand_koma_count(Side.GOTE, ktype, count)
        for ktype, count in read_hand(line_sente_hand):
            pos.set_hand_koma_count(Side.SENTE, ktype, count)
        
        # Board
        for r_idx, line in enumerate(lines[3:-2]):
            rank_str = line.split("|")[1]
            rank = [rank_str[i:i+2] for i in range(0, len(rank_str), 2)]
            for c_idx, pc_str in enumerate(rank):
                ktype = KTYPE_FROM_KANJI[pc_str[1]]
                side = Side.GOTE if pc_str[0] == "v" else Side.SENTE
                koma = Koma.make(side, ktype)
                pos.set_koma(koma, Square.from_cr(col_num=9-c_idx, row_num=r_idx+1))
        movetree.start_pos = pos.to_sfen()
        return
    
    def visit_handicap(self, reader: Reader, line: str) -> None:
        pos = reader.game.position
        movetree = reader.game.movetree
        val = line.split("：")[1]
        try:
            pos.from_sfen(SFEN_FROM_HANDICAP[val])
            movetree.handicap = val
            movetree.start_pos = SFEN_FROM_HANDICAP[val]
        except KeyError:
            # To handle elegantly? Maybe the rest is still valid.
            pass
        return
    
    def visit_move(self, reader: Reader, line: str) -> None:
        match = re.search(KIF_MOVELINE_REGEX, line)
        if match is None:
            raise TypeError("Match object is None, cannot identify move")
        else:
            movenum = match.group("movenum")
            movestr = match.group("move")
            movetime = match.group("movetime")
            totaltime = match.group("totaltime")
            move: Move
            if movestr in GameTermination:
                move = TerminationMove(GameTermination(movestr))
            else:
                m = re.search(KIF_MOVE_REGEX, movestr)
                if m is None:
                    raise ValueError("KIF move regex failed to match movestr: " + movestr)
                dest = m.group("sq_dest")
                komastr = m.group("koma")
                drop_prom = m.group("drop_prom")
                sq_origin = m.group("sq_origin")
                # Find destination square
                if dest == "同　":
                    end_sq = reader.game.curr_node.move.end_sq
                    captured = reader.game.position.get_koma(sq=end_sq)
                else:
                    col = int(dest[0])
                    row = int(KanjiNumber[dest[1]])
                    end_sq = Square.from_cr(col, row)
                    captured = reader.game.position.get_koma(sq=end_sq)
                ktype: KomaType
                if komastr[0] == "成":
                    ktype = KTYPE_FROM_KANJI[komastr[1]]
                    ktype = ktype.promote()
                else:
                    try:
                        ktype = KTYPE_FROM_KANJI[komastr]
                    except KeyError as e:
                        #TODO: handle gracefully and skip game
                        raise KeyError("Unknown koma encountered: " + komastr) from e
                # Find origin square
                if drop_prom != "打":
                    start_sq = Square.from_coord(int(sq_origin))
                else:
                    if ktype not in HAND_TYPES:
                        raise ValueError("Koma " + str(ktype) + " cannot be dropped")
                    start_sq = Square.HAND # Not NONE, not on board
                # Identify if promotion
                is_promotion = (drop_prom == "成")
                # Construct Move
                side = Side.SENTE if (int(movenum) % 2 == 1) else Side.GOTE
                koma = Koma.make(side, ktype)
                move = Move(start_sq, end_sq, is_promotion, koma, captured)
            reader.game.make_move(move)
        return
    
    def visit_variation(self, reader: Reader, line: str) -> None:
        match = re.match(KIF_VARIATION_REGEX, line)
        if match is None:
            raise ValueError("KIF variation regex failed to match: " + line)
        else:
            var_movenum = int(match.group("movenum"))
            while (
                (not reader.game.curr_node.is_null())
                and reader.game.curr_node.movenum != var_movenum
            ):
                reader.game.prev()
            reader.game.prev() # Once more to reach the prior move
            if reader.game.curr_node.is_null():
                raise Exception("HALP desired movenum not found")
            return


class Reader:
    def __init__(self) -> None:
        self.game = Game()
        return
    
    def read(self, handle: typing.TextIO, visitor: ParserVisitor) -> None:
        pass


class KifReader(Reader):
    def __init__(self) -> None:
        self.game = Game()
        return
    
    def read(self, handle: typing.TextIO, visitor: ParserVisitor) -> None:
        self.game.reset()
        line = handle.readline()
        while line != "":
            line = line.lstrip().rstrip()
            if line == "":
                pass
            elif line.startswith("手合割："):
                visitor.visit_handicap(self, line)
            elif line.startswith("後手の持駒："):
                # Signals start of BOD, read all of it
                bod_lines = [line]
                while (not line.startswith("先手の持駒：")) and line:
                    line = handle.readline()
                    bod_lines.append(line.lstrip().rstrip())
                visitor.visit_board(self, bod_lines)
            elif line.startswith("手数--"):
                # movesection delineation, no action needed
                pass
            elif line[0].isdigit():
                # Signals a move; thus, requires moves to be numbered.
                visitor.visit_move(self, line)
            elif line.startswith("*"):
                visitor.visit_comment(self, line)
            elif line.startswith("#"):
                visitor.visit_escape(self, line)
            elif line.startswith("変化："):
                # Variation
                visitor.visit_variation(self, line)
            else:
                # Unknown line; skip it
                pass
            # MUST fallthrough to here to complete one while iteration
            line = handle.readline()
        return
