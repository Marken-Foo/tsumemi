from collections import Counter
from enum import Enum, IntEnum

import re


class Side(Enum):
    SENTE = 0
    GOTE = 1
    SHITATE = 0
    UWATE = 1


class Piece(Enum):
    NONE = ("", "", "* ", "")
    GYOKU = ("玉", "王", "OU", "K")
    HISHA = ("飛", "飛", "HI", "R")
    RYUU = ("龍", "竜", "RY", "+R")
    KAKU = ("角", "角", "KA", "B")
    UMA = ("馬", "馬", "UM", "+B")
    KIN = ("金", "金", "KI", "G")
    GIN = ("銀", "銀", "GI", "S")
    NARIGIN = ("全", "成銀", "NG", "+S")
    KEI = ("桂", "桂", "KE", "N")
    NARIKEI = ("圭", "成桂", "NK", "+N")
    KYOU = ("香", "香", "KY", "L")
    NARIKYOU = ("杏", "成香", "NY", "+L")
    FU = ("歩", "歩", "FU", "P")
    TOKIN = ("と", "と", "TO", "+P")
    
    def __init__(self, kanji, kanji_alt, CSA, sfen_sym):
        self.kanji = kanji
        self.kanji_alt = kanji_alt
        self.CSA = CSA
        self.sfen_sym = sfen_sym
        return
    
    def __str__(self):
        return self.kanji
    
    def to_sfen_symbol(self):
        return self.sfen_sym
    
    @classmethod
    def from_kanji(cls, kanji):
        for item in cls:
            if item.kanji == kanji or item.kanji_alt == kanji:
                return item
            else:
                pass
        raise ValueError(kanji + " is not a valid shogi piece")


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


class Position:
    def __init__(self):
        # sfen square order
        self.sente = [[Piece.NONE] * 9 for i in range(9)]
        self.gote = [[Piece.NONE] * 9 for i in range(9)]
        self.sente_hand = []
        self.gote_hand = []
        self.side_to_move = Side.SENTE
        return
    
    def to_sfen(self):
        sfen_elems = []
        for row_num in range(9):
            n = 0 # counter for number of contiguous blank squares
            for col_num in range(9):
                pc_sente = self.sente[row_num][col_num]
                pc_gote = self.gote[row_num][col_num]
                if pc_sente is not Piece.NONE:
                    if n != 0:
                        sfen_elems.append(str(n))
                        n = 0
                    sfen_elems.append(pc_sente.to_sfen_symbol().upper())
                elif pc_gote is not Piece.NONE:
                    if n != 0:
                        sfen_elems.append(str(n))
                        n = 0
                    sfen_elems.append(pc_gote.to_sfen_symbol().lower())
                else:
                    n += 1
                    if col_num == 8:
                        sfen_elems.append(str(n))
            sfen_elems.append("/")
        sfen_elems.pop(-1) # remove slash after last row_num
        sfen_elems.append(" ")
        side_char = "b" if self.side_to_move is Side.SENTE else "w"
        sfen_elems.append(side_char)
        sfen_elems.append(" ")
        # Append hand pieces
        if not self.sente_hand and not self.gote_hand:
            sfen_elems.append("-")
        else:
            c_shand = Counter(self.sente_hand)
            for piece, count in c_shand.items():
                if count != 1:
                    sfen_elems.append(str(count))
                sfen_elems.append(piece.to_sfen_symbol().upper())
            c_ghand = Counter(self.gote_hand)
            for piece, count in c_ghand.items():
                if count != 1:
                    sfen_elems.append(str(count))
                sfen_elems.append(piece.to_sfen_symbol().lower())
        sfen_elems.append(" ")
        # Append turn number
        sfen_elems.append("1") # placeholder
        return "".join(sfen_elems)


class KifReader:
    board = Position()
    moves = []
    
    def __init__(self):
        return
    
    def parse_hand(self, handle, line=""):
        if line:
            hand_line = line
        else:
            hand_line = handle.readline().lstrip().rstrip()
        hand_pieces = []
        hand_str = hand_line.split("：", maxsplit=1)[1] # full-width colon
        hand_str = hand_str.lstrip().rstrip()
        if hand_str == "なし":
            return hand_pieces
        hand = re.split("　| ", hand_str) # full-width or half-width space
        for entry in hand:
            piece_type = Piece.from_kanji(entry[0])
            if len(entry) == 1:
                num_piece = 1
            elif len(entry) == 2:
                num_piece = KanjiNumber[entry[1]]
            elif len(entry) == 3:
                # e.g. 十八 = 18; max for a shogi position should be 18 (pawns)
                num_piece = KanjiNumber[entry[1]] + KanjiNumber[entry[2]]
            hand_pieces.extend([piece_type] * num_piece)
        return hand_pieces
    
    def parse_board(self, handle):
        # Parses and stores BOD board representation, without pieces in hand.
        sente_board = [[Piece.NONE] * 9 for i in range(9)]
        gote_board = [[Piece.NONE] * 9 for i in range(9)]
        line = handle.readline() # "  ９ ８ ７ ６ ５ ４ ３ ２ １"
        line = handle.readline() # "+---------------------------+"
        for row_num in range(9):
            line = handle.readline()
            rank_str = line.split("|")[1]
            rank = [rank_str[i:i+2] for i in range(0, len(rank_str), 2)]
            for col_num in range(9):
                piece_str = rank[col_num]
                if piece_str[0] == "v":
                    gote_board[row_num][col_num] = Piece.from_kanji(piece_str[1])
                elif piece_str[0] == " " and piece_str[1] != "・":
                    sente_board[row_num][col_num] = Piece.from_kanji(piece_str[1])
        line = handle.readline() # "+---------------------------+"
        return (sente_board, gote_board)
    
    def parse_kif(self, handle):
        # takes in text, extracts board and moves, ignores metadata.
        # assumes file has no extraneous blank lines/whitespace lines
        self.moves = [] # clear state; I should do the same for the Position
        line = handle.readline()
        while line != "":
            line = line.lstrip().rstrip()
            if line == "": # after stripping whitespace
                pass
            # skip escapes and comments
            elif line.startswith("#") or line.startswith("*"):
                pass
            elif line.startswith("後手の持駒："):
                # Assume BOD starts and is contiguous, read the BOD
                self.board.gote_hand = self.parse_hand(handle, line=line)
                (self.board.sente, self.board.gote) = self.parse_board(handle)
                self.board.sente_hand = self.parse_hand(handle)
            elif line.startswith("後手番"):
                self.board.side_to_move = Side.GOTE
            elif line.startswith("変化"):
                # read away the variation without adding it to self.moves
                line = handle.readline().lstrip().rstrip()
                while line != "" and line[0].isdigit():
                    line = handle.readline().lstrip().rstrip()
                continue
            elif line[0].isdigit():
                move = line.split(" ")[1]
                self.moves.append(move)
            else:
                # don't know what to do, skip everything else.
                pass
            line = handle.readline()
