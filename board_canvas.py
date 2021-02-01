import os
import tkinter as tk

from collections import Counter
from enum import Enum
from PIL import Image, ImageTk

from kif_parser import KanjiNumber, Piece


def _resize_image(img, width, height):
    # take PIL image, return resized PhotoImage
    resized_img = img.resize((int(width), int(height)))
    return ImageTk.PhotoImage(resized_img)


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
    INTL = ("Internationalised symbols", os.path.relpath(r"static/images/pieces/international"))
    
    def __init__(self, desc, directory):
        self.desc = desc
        self.directory = directory
        return


class CmdApplySkin:
    # Command pattern
    def __init__(self, target):
        self.target = target
    
    def execute(self, skin):
        return self.target.apply_skin(skin)


class BoardMeasurements():
    # Constant proportions
    SQ_ASPECT_RATIO = 11 / 12
    KOMADAI_W_IN_SQ = 2
    INNER_W_PAD = 10
    INNER_H_PAD = 30
    
    def __init__(self, width, height):
        # could refactor into a dictionary perhaps?
        (
            self.sq_w, self.sq_h, self.komadai_w, self.w_pad, self.h_pad,
            self.komadai_piece_size, self.sq_text_size, self.komadai_text_size,
            self.coords_text_size, self.x_sq, self.y_sq
        ) = self.calculate_sizes(width, height)
        return
    
    def calculate_sizes(self, canvas_width, canvas_height):
        # Geometry: 9x9 shogi board, flanked by komadai area on either side
        max_sq_w = ((canvas_width - 2*self.INNER_W_PAD)
                    / (9 + 2*self.KOMADAI_W_IN_SQ))
        max_sq_h = (canvas_height - 2*self.INNER_H_PAD) / 9
        # Determine whether the width or the height is the limiting factor
        sq_w = min(max_sq_w, max_sq_h*self.SQ_ASPECT_RATIO)
        # Propagate other measurements
        sq_h = sq_w / self.SQ_ASPECT_RATIO
        komadai_w = sq_w * self.KOMADAI_W_IN_SQ
        if int(sq_w) == int(max_sq_w):
            w_pad = self.INNER_W_PAD
            h_pad = (canvas_height - 9*sq_h) / 2
        else:
            w_pad = (canvas_width - 2*komadai_w - 9*sq_w) / 2
            h_pad = self.INNER_H_PAD
        sq_text_size = int(sq_w * 7/10)
        komadai_piece_size = int(sq_w * 4/5)
        komadai_text_size = int(sq_w * 2/5)
        coords_text_size = int(sq_w * 2/9)
        
        def x_sq(i):
            return w_pad + komadai_w + sq_w * i
        def y_sq(j):
            return h_pad + sq_h * j
        
        res = (
            sq_w, sq_h, komadai_w, w_pad, h_pad, komadai_piece_size,
            sq_text_size, komadai_text_size, coords_text_size,
            x_sq, y_sq
        )
        (
            self.sq_w, self.sq_h, self.komadai_w, self.w_pad, self.h_pad,
            self.komadai_piece_size, self.sq_text_size, self.komadai_text_size,
            self.coords_text_size, self.x_sq, self.y_sq
        ) = res
        return res


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
        self.piece_images_upright = {}
        self.piece_images_inverted = {}
        self.board_images = []
        
        # Specify source of board data
        self.reader = self.controller.model.reader
        config = self.controller.config # code should only read configparser
        # Initialise measurements, used for many other things
        self.measurements = BoardMeasurements(
            self.canvas_width, self.canvas_height
        )
        komadai_text_size = self.measurements.komadai_text_size
        try:
            name = config["skins"]["pieces"]
            self.piece_skin = PieceSkin[name]
        except KeyError:
            self.piece_skin = PieceSkin.TEXT
        try:
            name = config["skins"]["board"]
            self.board_skin = BoardSkin[name]
        except KeyError:
            self.board_skin = BoardSkin.WHITE
        self.load_piece_images(self.piece_skin)
        self.load_board_images(self.board_skin)
        return
    
    def load_piece_images(self, skin):
        sq_w = self.measurements.sq_w
        kpc_w = self.measurements.komadai_text_size*2
        if skin is PieceSkin.TEXT:
            # Text skin, no need images
            return
        for piece in Piece:
            if piece == Piece.NONE:
                continue
            filename = "0" + piece.CSA + ".png"
            img_path = os.path.join(skin.directory, filename)
            img = Image.open(img_path)
            photoimage = _resize_image(img, sq_w, sq_w)
            komadai_photoimage = _resize_image(img, kpc_w, kpc_w)
            self.piece_images_upright[piece] = [img, photoimage, komadai_photoimage]
            # inverted image
            filename = "1" + piece.CSA + ".png"
            img_path = os.path.join(skin.directory, filename)
            img = Image.open(img_path)
            photoimage = _resize_image(img, sq_w, sq_w)
            komadai_photoimage = _resize_image(img, kpc_w, kpc_w)
            self.piece_images_inverted[piece] = [img, photoimage, komadai_photoimage]
        return
    
    def load_board_images(self, skin):
        sq_w = self.measurements.sq_w
        sq_h = self.measurements.sq_h
        board_filename = skin.directory # Nonetype error?
        if board_filename:
            # assumes you want to TILE the image one per square.
            img = Image.open(board_filename)
            # The +1 pixel avoids gaps when tiling
            photoimage = _resize_image(img, sq_w+1, sq_h+1)
            self.board_images = [img, photoimage]
            return True
        else:
            return False
        
    def resize_images(self):
        sq_w = self.measurements.sq_w
        sq_h = self.measurements.sq_h
        kpc_w = self.measurements.komadai_text_size*2
        # resize piece images if using
        if self.piece_skin is not PieceSkin.TEXT:
            for piece in Piece:
                if piece == Piece.NONE:
                    continue
                img = self.piece_images_upright[piece][0]
                self.piece_images_upright[piece][1] = _resize_image(
                    img, sq_w, sq_w # assume square image
                )
                self.piece_images_upright[piece][2] = _resize_image(
                    img, kpc_w, kpc_w # assume square image
                )
                # inverted image
                img = self.piece_images_inverted[piece][0]
                self.piece_images_inverted[piece][1] = _resize_image(
                    img, sq_w, sq_w # assume square image
                )
                self.piece_images_inverted[piece][2] = _resize_image(
                    img, kpc_w, kpc_w # assume square image
                )
        # resize board image if using
        if self.board_skin.directory:
            img = self.board_images[0]
            self.board_images[1] = _resize_image(
                img, sq_w+1, sq_h+1 # +1 pixel avoids tiling gaps
            )
        return
    
    def draw_board(self):
        # Draws just the board, irrespective of the position.
        # Assumes board piece images are already loaded.
        # Komadai not included.
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        coords_text_size = self.measurements.coords_text_size
        row_coords = [" " + KanjiNumber(i).name for i in range(1, 10, 1)]
        col_coords = [str(i) for i in range(9, 0, -1)]
        if self.is_upside_down:
            row_coords.reverse()
            col_coords.reverse()
        # Draw board
        board_skin = self.board_skin
        board_filename = board_skin.directory
        # Colour board with solid colour
        self.board_rect = self.create_rectangle(
            x_sq(0), y_sq(0),
            x_sq(9), y_sq(9),
            fill=board_skin.colour
        )
        # Images created and stored so only their image field changes later.
        self.board_tiles = [[None] * 9 for i in range(9)]
        for row_num in range(9):
            for col_num in range(9):
                self.board_tiles[row_num][col_num] = self.create_image(
                    x_sq(row_num),
                    y_sq(col_num),
                    image="",
                    anchor="nw"
                )
        if board_filename:
            board_img = self.board_images[1]
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
        return
    
    def draw_piece(self, x, y, piece, komadai=False, invert=False, is_text=True, anchor="center"):
        text_size = self.measurements.komadai_text_size if komadai else self.measurements.sq_text_size
        if piece == Piece.NONE:
            return
        if is_text:
            self.create_text(
                x, y, text=str(piece.kanji),
                font=("", text_size),
                angle=180 if invert else 0,
                anchor=anchor
            )
        else:
            idx = 2 if komadai else 1
            img = (self.piece_images_inverted[piece][idx] if invert
                   else self.piece_images_upright[piece][idx])
            self.create_image(x, y, image=img, anchor=anchor)
        return
    
    def draw_komadai(self, x, y, hand, sente=True, align="top"):
        # draws a komadai with hand pieces, anchored "north" at (x, y).
        # does its own "anchoring" (align="top" or "bottom")
        komadai_text_size = self.measurements.komadai_text_size
        komadai_piece_size = self.measurements.komadai_piece_size
        is_text = (self.piece_skin is PieceSkin.TEXT)
        pad = -5 if is_text else 10
        
        c_hand = Counter(hand)
        # work out needed height
        num_piece_types = len(c_hand.items())
        if num_piece_types == 0:
            k_height = 9 * komadai_text_size
        else:
            k_height = 5.5*komadai_text_size + num_piece_types*(komadai_piece_size+10)-10
        if align == "bottom":
            # adjust the "anchor" point
            y = y - k_height
        
        header_text = "▲\n持\n駒" if sente else "△\n持\n駒"
        self.create_text(x, y, text=header_text, font=("", komadai_text_size), anchor="n")
        if not list(c_hand):
            # Hand is empty, write なし
            self.create_text(x, y+6*komadai_text_size, text="な\nし", anchor="n", font=("", komadai_text_size))
            return
        else:
            # Hand is not empty
            n = 0
            for piece, count in c_hand.items():
                self.draw_piece(x-0.4*komadai_piece_size, y+6*komadai_text_size+n*(komadai_piece_size+pad), piece=piece, komadai=True, is_text=is_text, anchor="center")
                self.create_text(x+0.5*komadai_piece_size, y+6*komadai_text_size+n*(komadai_piece_size+pad), text=str(count), font=("", komadai_text_size))
                n += 1
        return
    
    def draw(self):
        # Clear board display - could also keep board and just redraw pieces
        self.delete("all")
        reader = self.reader
        komadai_w = self.measurements.komadai_w
        w_pad = self.measurements.w_pad
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        
        # Gather north and south side data.
        # Note: if is_upside_down, essentially performs a deep copy,
        # but just "passes by reference" the reader's board if not.
        south_hand = reader.board.sente_hand
        north_hand = reader.board.gote_hand
        south_board = reader.board.sente
        north_board = reader.board.gote
        is_north_sente = False
        
        if self.is_upside_down:
            # swap hands
            north_hand, south_hand = south_hand, north_hand
            # "rotate" each board 180 degrees, then swap
            north_board = north_board[::-1]
            south_board = south_board[::-1]
            for i, row in enumerate(north_board):
                north_board[i] = row[::-1]
            for i, row in enumerate(south_board):
                south_board[i] = row[::-1]
            north_board, south_board = south_board, north_board
            is_north_sente = True
        
        # Draw board
        self.draw_board()
        
        # Draw board pieces
        is_text = (self.piece_skin is PieceSkin.TEXT)
        for row_num, row in enumerate(south_board):
            for col_num, piece in enumerate(row):
                self.draw_piece(
                    x_sq(col_num+0.5), y_sq(row_num+0.5), piece,
                    is_text=is_text
                )
        for row_num, row in enumerate(north_board):
            for col_num, piece in enumerate(row):
                self.draw_piece(
                    x_sq(col_num+0.5), y_sq(row_num+0.5), piece,
                    is_text=is_text,
                    invert=True
                )
        # Draw komadai
        self.draw_komadai(w_pad + komadai_w/3, y_sq(0), north_hand, sente=is_north_sente, align="top")
        self.draw_komadai(x_sq(9) + komadai_w*2/3, y_sq(9), south_hand, sente=not is_north_sente, align="bottom")
        return
    
    def apply_skin(self, skin):
        if isinstance(skin, PieceSkin):
            self.apply_piece_skin(skin)
        elif isinstance(skin, BoardSkin):
            self.apply_board_skin(skin)
        return
    
    def apply_piece_skin(self, skin):
        if skin is not PieceSkin.TEXT:
            self.load_piece_images(skin)
        komadai_text_size = self.measurements.komadai_text_size
        self.piece_skin = skin
        return
    
    def apply_board_skin(self, skin):
        sq_w = self.measurements.sq_w
        sq_h = self.measurements.sq_h
        komadai_text_size = self.measurements.komadai_text_size
        is_loaded = self.load_board_images(skin)
        self.itemconfig(self.board_rect, fill=skin.colour)
        board_img = self.board_images[1] if is_loaded else ""
        for row in self.board_tiles:
            for tile in row:
                self.itemconfig(tile, image=board_img)
        self.board_skin = skin
        return
    
    def on_resize(self, event):
        self.canvas_width = event.width
        self.canvas_height = event.height
        self.measurements.calculate_sizes(event.width, event.height)
        self.resize_images()
        komadai_text_size = self.measurements.komadai_text_size
        # Redraw board after setting new dimensions
        self.draw()
        return
    
    def flip_board(self, want_upside_down):
        if self.is_upside_down != want_upside_down:
            self.is_upside_down = want_upside_down
            self.draw()
        return
