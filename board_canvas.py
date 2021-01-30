import configparser
import os
import tkinter as tk

from collections import Counter, namedtuple
from enum import Enum
from tkinter import font
from PIL import Image, ImageTk

from kif_parser import KanjiNumber, Piece


# namedtuple mixin for Enum
Skin = namedtuple("Skin", ["desc", "directory"])

class PieceSkin(Skin, Enum):
    TEXT = Skin("1-kanji text characters", "")
    LIGHT = Skin("1-kanji light piece set by Ka-hu", os.path.relpath(r"static/images/pieces/kanji_light"))


class Komadai(tk.Frame):
    def __init__(self, parent, controller, sente=True, font=None, *args, **kwargs):
        self.controller = controller
        self.parent = parent
        self.font = font
        super().__init__(parent, *args, **kwargs)
        
        header_text = "▲\n持\n駒\n" if sente else "△\n持\n駒\n"
        self.header = tk.Label(self, text=header_text, font=self.font)
        self.header.grid(column=0, row=0, columnspan=2)
        
        self.nashi = tk.Label(self, text="な\nし", font=self.font)
        self.nashi.grid(column=0, row=1)
        
        cp = self.controller.config
        self.piece_skin = cp["skins"]["pieces"]
        self.hand_piece_types = (Piece.HISHA, Piece.KAKU, Piece.KIN, Piece.GIN, Piece.KEI, Piece.KYOU, Piece.FU)
        
        self.piece_labels = {}
        self.piece_counts = {}
        self.images = [] # avoid tkinter gc
        
        for n, piece in enumerate(self.hand_piece_types):
            self.piece_labels[piece] = tk.Label(self, text=str(piece), font=self.font)
            self.piece_labels[piece].grid(column=0, row=n+1)
            self.piece_labels[piece].grid_remove()
            self.piece_counts[piece] = tk.Label(self, text="0", font=self.font)
            self.piece_counts[piece].grid(column=1, row=n+1)
            self.piece_counts[piece].grid_remove()
        if self.piece_skin.upper() != "TEXT":
            self.init_images()
        return
    
    def init_images(self):
        # Contains Labels for each of the piece types - run this section iff
        # PIL available and iff the skin is not text.
        self.images = []
        for n, piece in enumerate(self.hand_piece_types):
            piece_filename = "0" + piece.CSA + ".png"
            piece_path = os.path.join(PieceSkin[self.piece_skin].directory,
                                      piece_filename)
            img = Image.open(piece_path)
            new_img = img.resize((int(40), int(40))) # assume square
            piece_img = ImageTk.PhotoImage(new_img)
            self.images.append(piece_img)
            self.piece_labels[piece]["image"] = piece_img
        return
    
    def draw(self, hand, sente=True):
        # Updates the komadai with new hand and sente information
        # sente is True/False, font is tuple for tkinter font and size
        self.header["text"] = "▲\n持\n駒\n" if sente else "△\n持\n駒\n"
        c_hand = Counter(hand)
        for label in self.piece_labels.values():
            label.grid_remove()
        for label in self.piece_counts.values():
            label.grid_remove()
        if not list(c_hand):
            # Hand is empty, write なし
            self.nashi.grid()
        else:
            # Hand is not empty
            self.nashi.grid_remove()
            for piece, count in c_hand.items():
                self.piece_counts[piece]["text"] = str(count)
                self.piece_counts[piece].grid()
                self.piece_labels[piece].grid()
        return
    
    def update_skin(self):
        # When new skin is selected
        cp = self.controller.config
        self.piece_skin = cp["skins"]["pieces"]
        if self.piece_skin.upper() == "TEXT":
            self.images = []
            for label in self.piece_labels.values():
                label["image"] = ""
        else:
            self.init_images()
        return


class BoardCanvas(tk.Canvas):
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
        
        # Specify source of board data
        self.reader = self.controller.model.reader
        self.config = self.controller.config # code should only read configparser
        
        (sq_w, sq_h, komadai_w, w_pad, h_pad, sq_text_size,
         komadai_text_size, coords_text_size,
         x_sq, y_sq) = self.calculate_sizes()
        
        self.south_komadai = Komadai(
            parent=self,
            controller=self.controller,
            sente=True,
            font=(font.nametofont("TkDefaultFont"), komadai_text_size)
        )
        self.south_komadai_window = self.create_window(
            x_sq(9) + komadai_w,
            y_sq(9),
            anchor="se",
            window=self.south_komadai
        )
        self.north_komadai = Komadai(
            parent=self,
            controller=self.controller,
            sente=False,
            font=(font.nametofont("TkDefaultFont"), komadai_text_size)
        )
        self.north_komadai_window = self.create_window(
            w_pad,
            y_sq(0),
            anchor="nw",
            window=self.north_komadai
        )
        return
    
    def draw(self):
        # Clear board display - could also keep board and just redraw pieces
        self.delete("all")
        self.images = []
        
        (sq_w, sq_h, komadai_w, w_pad, h_pad, sq_text_size,
         komadai_text_size, coords_text_size,
         x_sq, y_sq) = self.calculate_sizes()
        
        def _draw_piece(x, y, piece, invert=False):
            if piece == Piece.NONE:
                return
            piece_skin = self.config["skins"]["pieces"]
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
            south_hand = self.reader.board.sente_hand
            north_hand = self.reader.board.gote_hand
            south_board = self.reader.board.sente
            north_board = self.reader.board.gote
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
        self.south_komadai_window = self.create_window(
            x_sq(9) + komadai_w,
            y_sq(9),
            anchor="se",
            window=self.south_komadai
        )
        self.north_komadai_window = self.create_window(
            w_pad,
            y_sq(0),
            anchor="nw",
            window=self.north_komadai
        )
        self.south_komadai.draw(hand=south_hand, sente=not is_north_sente)
        self.north_komadai.draw(hand=north_hand, sente=is_north_sente)
        return
    
    def update_skin(self):
        self.north_komadai.update_skin()
        self.south_komadai.update_skin()
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
        
        def x_sq(i):
            return w_pad + komadai_w + sq_w * i
        def y_sq(j):
            return h_pad + sq_h * j
        
        return (sq_w, sq_h, komadai_w, w_pad, h_pad,
                sq_text_size, komadai_text_size, coords_text_size,
                x_sq, y_sq)
    
    def flip_board(self, want_upside_down):
        if self.is_upside_down != want_upside_down:
            self.is_upside_down = want_upside_down
            self.draw()
        return
