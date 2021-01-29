import configparser
import os

from collections import Counter, namedtuple
from enum import Enum
from PIL import Image, ImageTk
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
        self.images = [] # to avoid tkinter PhotoImage gc
        return
    
    def draw(self):
        # Specify source of board data
        reader = self.controller.model.reader
        cp = self.controller.config # code should only read configparser
        
        # Clear board display - could also keep board and just redraw pieces
        self.delete("all")
        self.images = []
        
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
                piece_filename = ("1" if invert else "0") + piece.CSA + ".png"
                piece_path = os.path.join(PieceSkin[piece_skin].directory,
                                          piece_filename)
                img = Image.open(piece_path)
                new_img = img.resize((int(sq_w), int(sq_w))) # assume square
                piece_img = ImageTk.PhotoImage(new_img)
                self.images.append(piece_img)
                self.create_image(x, y, image=piece_img)
            return
        
        def _draw_komadai_text(hand, north=True, sente=True):
            komadai_font = (font.nametofont("TkDefaultFont"), komadai_text_size)
            c_hand = Counter(hand)
            mochigoma_chars = ["▲"] if sente else ["△"]
            mochigoma_chars.append("\n持\n駒\n")
            if not list(c_hand):
                # Hand is empty, write なし
                mochigoma_chars.append("\nな\nし")
            else:
                for piece, count in c_hand.items():
                    mochigoma_chars.extend(["\n", str(piece), " ", str(count)])
            if north:
                self.create_text(
                    w_pad + komadai_w/2,
                    y_sq(0),
                    text="".join(mochigoma_chars),
                    font=komadai_font,
                    anchor="n"
                )
            else:
                self.create_text(
                    x_sq(9) + komadai_w/2,
                    y_sq(9),
                    text="".join(mochigoma_chars),
                    font=komadai_font,
                    anchor="s"
                )
            return
        
        def _draw_komadai(hand, north=True, sente=True):
            # if text, deal with it separately
            piece_skin = cp["skins"]["pieces"]
            if piece_skin.upper() == "TEXT":
                _draw_komadai_text(hand, north, sente)
                return
            komadai_font = (font.nametofont("TkDefaultFont"), komadai_text_size)
            c_hand = Counter(hand)
            mochigoma_chars = ["▲"] if sente else ["△"]
            mochigoma_chars.append("\n持\n駒\n")
            if not list(c_hand):
                # Hand is empty, write なし
                mochigoma_chars.append("\nな\nし")
            mochigoma_text = "".join(mochigoma_chars)
            if north:
                self.create_text(
                    w_pad + komadai_w/2,
                    y_sq(0),
                    text=mochigoma_text,
                    font=komadai_font,
                    anchor="n"
                )
            num = 2 if north else 9
            if list(c_hand):
                # hand is not empty
                x_displ = sq_w / 3
                x_pc = (w_pad + komadai_w/2 if north
                        else x_sq(9) + komadai_w*3/4)
                if north:
                    for piece, count in c_hand.items():
                        _draw_piece(x_pc - x_displ, y_sq(num + 0.3), piece)
                        self.create_text(
                            x_pc + x_displ,
                            y_sq(num + 0.3),
                            text=str(count),
                            font=komadai_font
                        )
                        num += 1
                else:
                    for piece, count in reversed(c_hand.items()):
                        _draw_piece(x_pc - x_displ, y_sq(num - 0.5), piece)
                        self.create_text(
                            x_pc + x_displ,
                            y_sq(num - 0.5),
                            text=str(count),
                            font=komadai_font
                        )
                        num -= 1
            if not north:
                self.create_text(
                    x_sq(9) + komadai_w*3/4,
                    y_sq(num),
                    text=mochigoma_text,
                    font=komadai_font,
                    anchor="s"
                )
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
            is_north_sente = True
            row_coords = [" " + KanjiNumber(i).name for i in range(9, 0, -1)]
            col_coords = [str(i) for i in range(1, 10, 1)]
        else:
            south_hand = reader.board.sente_hand
            north_hand = reader.board.gote_hand
            south_board = reader.board.sente
            north_board = reader.board.gote
            is_north_sente = False
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
                _draw_piece(x_sq(col_num+0.5), y_sq(row_num+0.5), piece,
                            invert=True)
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
        # Draw komadai pieces
        _draw_komadai(
            south_hand,
            north=False,
            sente=False if is_north_sente else True
        )
        _draw_komadai(
            north_hand,
            north=True,
            sente=True if is_north_sente else False
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
