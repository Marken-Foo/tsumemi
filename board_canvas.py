import configparser
import os

from collections import Counter, namedtuple
from enum import Enum
from tkinter import Canvas, PhotoImage
from tkinter import font

from kif_parser import KanjiNumber, Piece


# namedtuple mixin for Enum
Skin = namedtuple("Skin", ["desc", "directory"])

class PieceSkin(Skin, Enum):
    TEXT = Skin("1-kanji text characters", "")
    LIGHT = Skin("1-kanji light piece set by Ka-hu", os.path.relpath(r"static/images/pieces/kanji_light"))


class BoardCanvas(Canvas):
    '''Class encapsulating the canvas where the board is drawn.'''
    # Default/current canvas size for board
    canvas_width = 600
    canvas_height = 500
    
    # Constant proportions
    SQ_ASPECT_RATIO = 11 / 12
    KOMADAI_W_IN_SQ = 1.7
    INNER_H_PAD = 30
    
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        self.is_upside_down = False
        super().__init__(parent, *args, **kwargs)
        return
    
    def draw(self):
        # Specify source of board data
        reader = self.controller.model.reader
        cp = self.controller.config # code should only read configparser
        
        # Clear board display - could also keep board and just redraw pieces
        self.delete("all")
        
        (sq_w, sq_h, komadai_w, w_pad, h_pad, sq_text_size,
         komadai_text_size, coords_text_size) = self.calculate_sizes()
        def x_sq(i):
            return w_pad + komadai_w + sq_w * i
        def y_sq(j):
            return h_pad + sq_h * j
        
        def _draw_piece(x, y, piece, invert=False):
            if piece == Piece.NONE:
                return
            piece_skin = cp["skins"]["pieces"]
            angle = 180 if invert else 0
            if piece_skin.upper() == "TEXT":
                self.create_text(
                    x, y, text=str(piece.kanji),
                    font=(font.nametofont("TkDefaultFont"), sq_text_size),
                    angle=angle
                )
            else:
                piece_filename = ("1" if invert else "0") + piece.CSA + ".svg"
                piece_img = PhotoImage(file=os.path.join(PieceSkin[piece_skin].directory, piece_filename))
                self.create_image(x, y, image=piece_img)
            return
        
        # Note: if is_upside_down, essentially performs a deep copy,
        # but just "passes by reference" the reader's board if not.
        if self.is_upside_down:
            south_hand = reader.board.gote_hand
            north_hand = reader.board.sente_hand
            south_board = reader.board.gote[::-1]
            north_board = reader.board.sente[::-1]
            for i, row in enumerate(south_board):
                south_board[i] = row[::-1]
            for i, row in enumerate(north_board):
                north_board[i] = row[::-1]
            south_hand_strings = ["△\n持\n駒\n"]
            north_hand_strings = ["▲\n持\n駒\n"]
            row_coords = [" " + KanjiNumber(i).name for i in range(9, 0, -1)]
            col_coords = [str(i) for i in range(1, 10, 1)]
        else:
            south_hand = reader.board.sente_hand
            north_hand = reader.board.gote_hand
            south_board = reader.board.sente
            north_board = reader.board.gote
            south_hand_strings = ["▲\n持\n駒\n"]
            north_hand_strings = ["△\n持\n駒\n"]
            row_coords = [" " + KanjiNumber(i).name for i in range(1, 10, 1)]
            col_coords = [str(i) for i in range(9, 0, -1)]
        
        # Draw board
        for i in range(10):
            self.create_line(x_sq(i), y_sq(0), x_sq(i), y_sq(9),
                                    fill="black", width=1)
            self.create_line(x_sq(0), y_sq(i), x_sq(9), y_sq(i),
                                    fill="black", width=1)
        # Draw board pieces
        for row_num, row in enumerate(south_board):
            for col_num, piece in enumerate(row):
                _draw_piece(x_sq(col_num+0.5), y_sq(row_num+0.5), piece)
        for row_num, row in enumerate(north_board):
            for col_num, piece in enumerate(row):
                _draw_piece(x_sq(col_num+0.5), y_sq(row_num+0.5), piece, invert=True)
        # Draw board coordinates
        for row_num in range(9):
            self.create_text(
                x_sq(9), y_sq(row_num+0.5),
                text=" " + row_coords[row_num],
                font=(font.nametofont("TkDefaultFont"), coords_text_size),
                anchor="w"
            )
        for col_num in range(9):
            self.create_text(
                x_sq(col_num+0.5), y_sq(0),
                text=col_coords[col_num],
                font=(font.nametofont("TkDefaultFont"), coords_text_size),
                anchor="s"
            )
        # Draw sente hand pieces
        c = Counter(south_hand)
        for piece in c:
            south_hand_strings.append(str(piece) + str(c[piece]))
        if len(south_hand_strings) == 1:
            south_hand_strings.append("な\nし")
        self.create_text(
            x_sq(9) + komadai_w, y_sq(9),
            text="\n".join(south_hand_strings),
            font=(font.nametofont("TkDefaultFont"), komadai_text_size),
            anchor="se"
        )
        # Draw gote hand pieces
        c = Counter(north_hand)
        for piece in c:
            north_hand_strings.append(str(piece) + str(c[piece]))
        if len(north_hand_strings) == 1:
            north_hand_strings.append("な\nし")
        self.create_text(
            w_pad, h_pad,
            text="\n".join(north_hand_strings),
            font=(font.nametofont("TkDefaultFont"), komadai_text_size),
            anchor="nw"
        )
        return
    
    def on_resize(self, event):
        self.canvas_width = event.width
        self.canvas_height = event.height
        # Redraw board after setting new dimensions
        self.draw()
        return
    
    def calculate_sizes(self):
        # Geometry: 9x9 shogi board, flanked by komadai area on either side
        max_sq_w = self.canvas_width / (9 + 2*self.KOMADAI_W_IN_SQ)
        max_sq_h = (self.canvas_height - 2*self.INNER_H_PAD) / 9
        # Determine whether the width or the height is the limiting factor
        sq_w = min(max_sq_w, max_sq_h*self.SQ_ASPECT_RATIO)
        # Propagate other measurements
        sq_h = sq_w / self.SQ_ASPECT_RATIO
        komadai_w = sq_w * self.KOMADAI_W_IN_SQ
        if sq_w == max_sq_w:
            w_pad = 0
            h_pad = self.INNER_H_PAD + (self.canvas_height - 9*sq_h) / 2
        else:
            w_pad = (self.canvas_width - 2*komadai_w - 9*sq_w) / 2
            h_pad = self.INNER_H_PAD
        sq_text_size = int(sq_w * 7/10)
        komadai_text_size = int(sq_w * 2/5)
        coords_text_size = int(sq_w * 2/9)
        return (sq_w, sq_h, komadai_w, w_pad, h_pad,
                sq_text_size, komadai_text_size, coords_text_size)
    
    def flip_board(self, want_upside_down):
        if self.is_upside_down != want_upside_down:
            self.is_upside_down = want_upside_down
            self.draw()
        return
