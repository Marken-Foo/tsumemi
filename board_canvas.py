import configparser
import os
import tkinter as tk

from collections import Counter
from enum import Enum
from PIL import Image, ImageTk

from kif_parser import KanjiNumber, Piece


class BoardSkin(Enum):
    WHITE = ("solid white", "white", "")
    BROWN = ("solid brown", "burlywood1", "")
    WOOD2 = ("Wood2", "", os.path.relpath(r"static/images/boards/tile_wood2.png"))
    
    def __init__(self, desc, colour, directory):
        self.desc = desc
        self.colour = colour
        self.directory = directory


class PieceSkin(Enum):
    TEXT = ("1-kanji text characters", "")
    LIGHT = ("1-kanji light pieces", os.path.relpath(r"static/images/pieces/kanji_light"))
    
    def __init__(self, desc, directory):
        self.desc = desc
        self.directory = directory
        return


class Komadai(tk.Frame):
    def __init__(self, parent, controller, sente=True, font="", *args, **kwargs):
        self.controller = controller
        self.parent = parent
        self.font = font
        super().__init__(parent, *args, **kwargs)
        
        header_text = "▲\n持\n駒\n" if sente else "△\n持\n駒\n"
        self.header = tk.Label(self, text=header_text, font=font)
        self.header.grid(column=0, row=0, columnspan=2)
        
        self.nashi = tk.Label(self, text="な\nし", font=font)
        self.nashi.grid(column=0, row=1)
        
        cp = controller.config
        self.piece_skin = cp["skins"]["pieces"]
        self.hand_piece_types = (Piece.HISHA, Piece.KAKU, Piece.KIN, Piece.GIN, Piece.KEI, Piece.KYOU, Piece.FU)
        
        self.piece_labels = {}
        self.piece_counts = {}
        self.images = [] # avoid tkinter gc
        
        for n, piece in enumerate(self.hand_piece_types):
            lbl_piece = self.piece_labels[piece] = tk.Label(self, text=str(piece), font=font)
            lbl_piece.grid(column=0, row=n+1)
            lbl_piece.grid_remove()
            lbl_count = self.piece_counts[piece] = tk.Label(self, text="0", font=font)
            lbl_count.grid(column=1, row=n+1)
            lbl_count.grid_remove()
        if not self.is_skin_text():
            self.init_images(40) # um what?
        
        self["background"] = "white"
        for child in self.winfo_children():
            child["background"] = "white"
        return
    
    def is_skin_text(self):
        return self.piece_skin.upper() == "TEXT"
    
    def init_images(self, img_w):
        # Contains Labels for each of the piece types - run this section iff
        # PIL available and iff the skin is not text.
        self.images = []
        for n, piece in enumerate(self.hand_piece_types):
            piece_filename = "0" + piece.CSA + ".png"
            piece_path = os.path.join(PieceSkin[self.piece_skin].directory,
                                      piece_filename)
            img = Image.open(piece_path)
            img = img.resize((int(img_w), int(img_w))) # assume square
            piece_img = ImageTk.PhotoImage(img)
            self.images.append(piece_img)
            self.piece_labels[piece]["image"] = piece_img
        return
    
    def update(self, hand, sente=True):
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
    
    def update_skin(self, img_w):
        # When new skin is selected
        cp = self.controller.config
        self.piece_skin = cp["skins"]["pieces"]
        if self.is_skin_text():
            self.images = []
            for label in self.piece_labels.values():
                label["image"] = ""
        else:
            self.init_images(img_w)
        return
    
    def on_resize(self, text_size, img_size):
        self.header["font"] = ("", text_size)
        self.nashi["font"] = ("", text_size)
        for label in self.piece_labels.values():
            label["font"] = ("", text_size)
        for label in self.piece_counts.values():
            label["font"] = ("", text_size)
        if not self.is_skin_text():
            self.init_images(img_size)
        return


class BoardCanvas(tk.Canvas):
    '''Class encapsulating the canvas where the board is drawn.'''
    # Default/current canvas size for board
    canvas_width = 600
    canvas_height = 500
    
    # Constant proportions
    SQ_ASPECT_RATIO = 11 / 12
    KOMADAI_W_IN_SQ = 2
    INNER_H_PAD = 30
    
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        self.is_upside_down = False
        super().__init__(parent, *args, **kwargs)
        self.images = [] # to avoid tkinter PhotoImage gc
        
        # Specify source of board data
        self.reader = self.controller.model.reader
        self.config = self.controller.config # code should only read configparser
        
        _, _, _, _, _, _, komadai_text_size, _, _, _ = self._calculate_sizes()
        
        self.south_komadai = Komadai(
            parent=self,
            controller=self.controller,
            sente=True,
            font=("", komadai_text_size)
        )
        self.north_komadai = Komadai(
            parent=self,
            controller=self.controller,
            sente=False,
            font=("", komadai_text_size)
        )
        return
    
    def draw(self):
        # Clear board display - could also keep board and just redraw pieces
        self.delete("all")
        self.images = []
        reader = self.reader
        
        # Avoid self hell by calculating
        (sq_w, sq_h, komadai_w, w_pad, _, sq_text_size,
         komadai_text_size, coords_text_size,
         x_sq, y_sq) = self._calculate_sizes()
        
        def _draw_piece(x, y, piece, invert=False):
            if piece == Piece.NONE:
                return
            piece_skin = self.config["skins"]["pieces"]
            angle = 180 if invert else 0
            if piece_skin.upper() == "TEXT":
                self.create_text(
                    x, y, text=str(piece.kanji),
                    font=("", sq_text_size),
                    angle=angle
                )
            else:
                piece_filename = ("1" if invert else "0") + piece.CSA + ".png"
                piece_path = os.path.join(PieceSkin[piece_skin].directory,
                                          piece_filename)
                img = Image.open(piece_path)
                img = img.resize((int(sq_w), int(sq_w))) # assume square
                piece_img = ImageTk.PhotoImage(img)
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
            south_hand = reader.board.sente_hand
            north_hand = reader.board.gote_hand
            south_board = reader.board.sente
            north_board = reader.board.gote
            is_north_sente = False
            row_coords = [" " + KanjiNumber(i).name for i in range(1, 10, 1)]
            col_coords = [str(i) for i in range(9, 0, -1)]
        
        # Draw board
        board_skin = BoardSkin[self.config["skins"]["board"]]
        board_filename = board_skin.directory
        self.board_rect = self.create_rectangle(x_sq(0), y_sq(0), x_sq(9), y_sq(9), fill=board_skin.colour)
        self.board_tiles = [[None] * 9 for i in range(9)]
        for row_num in range(9):
            for col_num in range(9):
                self.board_tiles[row_num][col_num] = self.create_image(x_sq(row_num+0.5), y_sq(col_num+0.5), image="")
        if board_filename:
            # assumes you want to TILE the image one per square.
            img = Image.open(board_filename)
            img = img.resize((int(sq_w), int(sq_h)))
            board_img = ImageTk.PhotoImage(img)
            self.images.append(board_img)
            for row in self.board_tiles:
                for tile in row:
                    self.itemconfig(tile, image=board_img)
        for i in range(10):
            self.create_line(x_sq(i), y_sq(0), x_sq(i), y_sq(9),
                                    fill="black", width=1)
            self.create_line(x_sq(0), y_sq(i), x_sq(9), y_sq(i),
                                    fill="black", width=1)
        # Draw board coordinates
        for row_num in range(9):
            self.create_text(
                x_sq(9), y_sq(row_num+0.5),
                text=" " + row_coords[row_num],
                font=("", coords_text_size),
                anchor="w"
            )
        for col_num in range(9):
            self.create_text(
                x_sq(col_num+0.5), y_sq(0),
                text=col_coords[col_num],
                font=("", coords_text_size),
                anchor="s"
            )
        # Draw board pieces
        for row_num, row in enumerate(south_board):
            for col_num, piece in enumerate(row):
                _draw_piece(x_sq(col_num+0.5), y_sq(row_num+0.5), piece)
        for row_num, row in enumerate(north_board):
            for col_num, piece in enumerate(row):
                _draw_piece(x_sq(col_num+0.5), y_sq(row_num+0.5), piece,
                            invert=True)
        # Draw komadai pieces
        self.create_window(
            x_sq(9) + komadai_w*2/3,
            y_sq(9),
            anchor="s",
            window=self.south_komadai
        )
        self.create_window(
            w_pad + komadai_w/3,
            y_sq(0),
            anchor="n",
            window=self.north_komadai
        )
        self.south_komadai.update(hand=south_hand, sente=not is_north_sente)
        self.north_komadai.update(hand=north_hand, sente=is_north_sente)
        return
    
    def update_skin(self):
        _, _, _, _, _, _, komadai_text_size, _, _, _ = self._calculate_sizes()
        self.north_komadai.update_skin(komadai_text_size*2)
        self.south_komadai.update_skin(komadai_text_size*2)
        return
    
    def update_board(self):
        sq_w, sq_h, _, _, _, _, komadai_text_size, _, _, _ = self._calculate_sizes()
        board_skin = BoardSkin[self.config["skins"]["board"]]
        board_filename = board_skin.directory
        self.itemconfig(self.board_rect, fill=board_skin.colour)
        if board_filename:
            img = Image.open(board_filename)
            img = img.resize((int(sq_w), int(sq_h)))
            board_img = ImageTk.PhotoImage(img)
            self.images.append(board_img)
            for row in self.board_tiles:
                for tile in row:
                    self.itemconfig(tile, image=board_img)
        else:
            for row in self.board_tiles:
                for tile in row:
                    self.itemconfig(tile, image="")
        return
    
    def on_resize(self, event):
        self.canvas_width = event.width
        self.canvas_height = event.height
        _, _, _, _, _, _, komadai_text_size, _, _, _ = self._calculate_sizes()
        self.north_komadai.on_resize(komadai_text_size, komadai_text_size*2)
        self.south_komadai.on_resize(komadai_text_size, komadai_text_size*2)
        # Redraw board after setting new dimensions
        self.draw()
        return
    
    def _calculate_sizes(self):
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
