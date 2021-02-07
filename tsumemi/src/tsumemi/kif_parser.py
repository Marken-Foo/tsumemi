from enum import Enum, IntEnum
import re


class Piece(Enum):
    NONE = ("", "", "* ")
    GYOKU = ("玉", "王", "OU")
    HISHA = ("飛", "飛", "HI")
    RYUU = ("龍", "竜", "RY")
    KAKU = ("角", "角", "KA")
    UMA = ("馬", "馬", "UM")
    KIN = ("金", "金", "KI")
    GIN = ("銀", "銀", "GI")
    NARIGIN = ("全", "成銀", "NG")
    KEI = ("桂", "桂", "KE")
    NARIKEI = ("圭", "成桂", "NK")
    KYOU = ("香", "香", "KY")
    NARIKYOU = ("杏", "成香", "NY")
    FU = ("歩", "歩", "FU")
    TOKIN = ("と", "と", "TO")
    
    def __init__(self, kanji, kanji_alt, CSA):
        self.kanji = kanji
        self.kanji_alt = kanji_alt
        self.CSA = CSA
        return
    
    def __str__(self):
        return self.kanji
    
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
    # sfen square order
    sente = [[Piece.NONE] * 9 for i in range(9)]
    gote = [[Piece.NONE] * 9 for i in range(9)]
    sente_hand = []
    gote_hand = []
    side_to_move = 0 # sente = 0
    
    def __init__(self):
        pass


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
