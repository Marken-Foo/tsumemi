import os
import tkinter as tk

from abc import ABC, abstractmethod
from collections import Counter
from enum import Enum
from PIL import Image, ImageTk

from tsumemi.src.shogi.basetypes import KanjiNumber, Koma, KomaType, Side, HAND_TYPES, KANJI_FROM_KTYPE


BOARD_IMAGES_PATH = os.path.relpath(r"tsumemi/resources/images/boards") 
PIECE_IMAGES_PATH = os.path.relpath(r"tsumemi/resources/images/pieces")


class BoardSkin(Enum):
    WHITE = ("solid white", "white", None)
    BROWN = ("solid brown", "burlywood1", None)
    WOOD1 = ("Wood1", "#d29a00", os.path.join(BOARD_IMAGES_PATH, r"tile_wood1.png"))
    WOOD2 = ("Wood2", "#fbcd77", os.path.join(BOARD_IMAGES_PATH, r"tile_wood2.png"))
    WOOD3 = ("Wood3", "#c98e52", os.path.join(BOARD_IMAGES_PATH, r"tile_wood3.png"))
    WOOD4 = ("Wood4", "#d5b45a", os.path.join(BOARD_IMAGES_PATH, r"tile_wood4.png"))
    WOOD5 = ("Wood5", "#ffdf8f", os.path.join(BOARD_IMAGES_PATH, r"tile_wood5.png"))
    WOOD6 = ("Wood6", "#f4ca64", os.path.join(BOARD_IMAGES_PATH, r"tile_wood6.png"))
    STONE = ("Stone", "#b8b9af", os.path.join(BOARD_IMAGES_PATH, r"tile_stone.png"))
    MILITARY = ("Military", "#a06b3a", os.path.join(BOARD_IMAGES_PATH, r"tile_military.png"))
    MILITARY2 = ("Military2", "#bd7b32", os.path.join(BOARD_IMAGES_PATH, r"tile_military2.png"))
    
    def __init__(self, desc, colour, path):
        self.desc = desc
        self.colour = colour
        self.path = path


class PieceSkin(Enum):
    TEXT = ("1-kanji text characters", None)
    LIGHT = ("1-kanji light pieces", os.path.join(PIECE_IMAGES_PATH, r"kanji_light"))
    BROWN = ("1-kanji brown pieces", os.path.join(PIECE_IMAGES_PATH, r"kanji_brown"))
    REDWOOD = ("1-kanji red wood pieces", os.path.join(PIECE_IMAGES_PATH, r"kanji_red_wood"))
    INTL = ("Internationalised symbols", os.path.join(PIECE_IMAGES_PATH, r"international"))
    
    def __init__(self, desc, path):
        self.desc = desc
        self.path = path
        return


class ImgResizer:
    """Take PIL Image and store it alongside a resized
    ImageTk.PhotoImage. Manage resized dimensions via function passed
    in constructor. Responsible for resizing images to correct
    dimensions.
    """
    def __init__(self, update_func):
        self.update_func = update_func # function returns tuple (width, height)
        self.width, self.height = update_func()
        self.raws = {}
        self.images = {}
        return
    
    def _resize_image(self, img, width, height):
        """Take PIL Image img, return resized ImageTk.PhotoImage.
        """
        resized_img = img.resize((int(width), int(height)))
        return ImageTk.PhotoImage(resized_img)
    
    def add_image(self, key, image):
        self.raws[key] = image
        self.images[key] = self._resize_image(image, self.width, self.height)
        return
    
    def resize_images(self):
        for key in self.raws:
            self.images[key] = self._resize_image(
                self.raws[key], self.width, self.height
            )
        return
    
    def update_sizes(self):
        self.width, self.height = self.update_func()
        return
    
    def get_dict(self):
        return self.images


class ImgManager(ABC):
    def has_images(self):
        return self.skin.path is not None
    
    @abstractmethod
    def load(self, skin):
        pass
    
    @abstractmethod
    def resize_images(self):
        pass


class PieceImgManager(ImgManager):
    def __init__(self, measurements, skin):
        def _komadai_piece_size():
            kpc_w = measurements.komadai_piece_size
            return kpc_w, kpc_w
        def _board_piece_size():
            sq_w = measurements.sq_w
            return sq_w, sq_w
        self.upright = ImgResizer(_board_piece_size)
        self.inverted = ImgResizer(_board_piece_size)
        self.komadai_upright = ImgResizer(_komadai_piece_size)
        self.komadai_inverted = ImgResizer(_komadai_piece_size)
        self.measurements = measurements
        self.load(skin)
        self.skin = skin
        return
    
    def has_images(self):
        return (self.skin.path is not None)
    
    def load(self, skin):
        filepath = skin.path
        if filepath:
            for ktype in KomaType:
                if ktype == KomaType.NONE:
                    continue
                filename = "0" + ktype.to_csa() + ".png"
                img_path = os.path.join(skin.path, filename)
                img = Image.open(img_path)
                self.upright.add_image(ktype, img)
                self.komadai_upright.add_image(ktype, img)
                # upside-down image
                filename = "1" + ktype.to_csa() + ".png"
                img_path = os.path.join(skin.path, filename)
                img = Image.open(img_path)
                self.inverted.add_image(ktype, img)
                self.komadai_inverted.add_image(ktype, img)
            self.skin = skin
            return
        else:
            # skin without images
            self.skin = skin
            return
    
    def resize_images(self):
        if self.skin.path:
            imgdicts = (
                self.upright,
                self.inverted,
                self.komadai_upright,
                self.komadai_inverted
            )
            for imgdict in imgdicts:
                imgdict.update_sizes()
                imgdict.resize_images()
        return
    
    def get_dict(self, invert=False, komadai=False):
        if not invert and not komadai:
            return self.upright.get_dict()
        elif invert and not komadai:
            return self.inverted.get_dict()
        elif not invert and komadai:
            return self.komadai_upright.get_dict()
        else: # invert and komadai
            return self.komadai_inverted.get_dict()


class BoardImgManager(ImgManager):
    def __init__(self, measurements, skin):
        def _board_sq_size():
            sq_w = measurements.sq_w
            sq_h = measurements.sq_h
            # +1 pixel to avoid gaps when tiling image
            return sq_w+1, sq_h+1
        self.images = ImgResizer(_board_sq_size)
        self.measurements = measurements
        self.load(skin)
        self.skin = skin
        return
    
    def load(self, skin):
        filepath = skin.path
        if filepath:
            img = Image.open(filepath)
            self.images.add_image("board", img)
            self.skin = skin # after loading, in case anything goes wrong
            return
        else:
            # skin without images
            self.skin = skin
            return
    
    def resize_images(self):
        if self.skin.path:
            imgdicts = (self.images,)
            for imgdict in imgdicts:
                imgdict.update_sizes()
                imgdict.resize_images()
        return
    
    def get_dict(self):
        return self.images.get_dict()


class BoardMeasurements:
    """Parameter object calculating and storing the various measurements of the
    shogiban.
    """
    INNER_H_PAD = 30 # pixels
    INNER_W_PAD = 10 # pixels
    # Constant proportions; base unit is square width.
    COORD_TEXT_IN_SQ = 2/9
    KOMADAI_PIECE_RATIO = 4/5 # komadai piece : board piece size ratio
    KOMADAI_TEXT_IN_SQ = 2/5
    KOMADAI_W_IN_SQ = 2
    SQ_ASPECT_RATIO = 11/12
    SQ_TEXT_IN_SQ = 7/10
    
    def __init__(self, width, height):
        # could refactor into a dictionary perhaps?
        (
            self.sq_w, self.sq_h, self.komadai_w, self.w_pad, self.h_pad,
            self.komadai_piece_size, self.sq_text_size, self.komadai_text_size,
            self.coords_text_size, self.x_sq, self.y_sq
        ) = self.recalculate_sizes(width, height)
        return
    
    def recalculate_sizes(self, canvas_width, canvas_height):
        """Geometry: 9x9 shogi board, flanked by komadai area on either side.
        Padded on all 4 sides (canvas internal padding).
        Extra space allocated between board and right komadai (2 times coord
        text size) to accomodate board coordinates drawn there.
        """
        max_sq_w = ((canvas_width - 2*self.INNER_W_PAD)
                    / (9 + 2*self.KOMADAI_W_IN_SQ + 2*self.COORD_TEXT_IN_SQ))
        max_sq_h = (canvas_height - 2*self.INNER_H_PAD) / 9
        # Determine whether the width or the height is the limiting factor
        sq_w = min(max_sq_w, max_sq_h*self.SQ_ASPECT_RATIO)
        # Propagate other measurements
        sq_h = sq_w / self.SQ_ASPECT_RATIO
        coords_text_size = int(sq_w * self.COORD_TEXT_IN_SQ)
        komadai_piece_size = int(sq_w * self.KOMADAI_PIECE_RATIO)
        komadai_text_size = int(sq_w * self.KOMADAI_TEXT_IN_SQ)
        komadai_w = sq_w * self.KOMADAI_W_IN_SQ
        sq_text_size = int(sq_w * self.SQ_TEXT_IN_SQ)
        if int(sq_w) == int(max_sq_w):
            w_pad = self.INNER_W_PAD
            h_pad = (canvas_height - 9*sq_h) / 2
        else:
            w_pad = (canvas_width - 2*komadai_w
                     - 2*coords_text_size - 9*sq_w) / 2
            h_pad = self.INNER_H_PAD
        # Useful helper functions. Argument is row/col number of square.
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
    """The canvas where the shogi position is drawn. Responsible for drawing on
    itself, delegating other tasks like size calculation to other objects.
    """
    # Default/current canvas size for board
    CANVAS_WIDTH = 600
    CANVAS_HEIGHT = 500
    
    def __init__(self, parent, controller, position, *args, **kwargs):
        self.controller = controller
        self.is_upside_down = False
        super().__init__(parent, *args, **kwargs)
        # Specify source of board data
        self.position = position
        config = self.controller.config
        # Initialise measurements, used for many other things
        self.measurements = BoardMeasurements(
            self.CANVAS_WIDTH, self.CANVAS_HEIGHT
        )
        try:
            name = config["skins"]["pieces"]
            piece_skin = PieceSkin[name]
        except KeyError:
            piece_skin = PieceSkin.TEXT
        try:
            name = config["skins"]["board"]
            board_skin = BoardSkin[name]
        except KeyError:
            board_skin = BoardSkin.WHITE
        try:
            name = config["skins"]["komadai"]
            komadai_skin = BoardSkin[name]
        except KeyError:
            komadai_skin = BoardSkin.WHITE
        self.piece_images = PieceImgManager(self.measurements, piece_skin)
        self.board_images = BoardImgManager(self.measurements, board_skin)
        self.komadai_skin = komadai_skin
        return
    
    def draw_board(self):
        """Draw just the shogiban, without pieces. Komadai areas not included.
        """
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        coords_text_size = self.measurements.coords_text_size
        row_coords = [" " + KanjiNumber(i).name for i in range(1, 10, 1)]
        col_coords = [str(i) for i in range(9, 0, -1)]
        if self.is_upside_down:
            row_coords.reverse()
            col_coords.reverse()
        # Draw board
        board_skin = self.board_images.skin
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
        if self.board_images.has_images():
            board_img = self.board_images.get_dict()["board"]
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
    
    def draw_koma(self, x, y, ktype, komadai=False, invert=False,
                   is_text=True, anchor="center"):
        if ktype == KomaType.NONE:
            return
        if is_text:
            text_size = (
                self.measurements.komadai_text_size
                if komadai
                else self.measurements.sq_text_size
            )
            self.create_text(
                x, y, text=str(KANJI_FROM_KTYPE[ktype]),
                font=("", text_size),
                angle=180 if invert else 0,
                anchor=anchor
            )
        else:
            piece_dict = self.piece_images.get_dict(
                invert=invert, komadai=komadai
            )
            img = piece_dict[ktype]
            self.create_image(x, y, image=img, anchor=anchor)
        return
    
    def draw_komadai(self, x, y, hand, sente=True, align="top"):
        """Draw komadai with pieces given by hand argument, anchored at canvas
        position (x, y). "Anchoring" north or south achieved with align="top"
        or "bottom".
        """
        # Note: actual size of each character in px is about 1.5*text_size
        komadai_text_size = self.measurements.komadai_text_size
        komadai_char_height = 1.5 * komadai_text_size
        komadai_piece_size = self.measurements.komadai_piece_size
        is_text = not self.piece_images.has_images()
        symbol_size = komadai_text_size*3/2 if is_text else komadai_piece_size
        pad = (komadai_text_size / 8 if is_text else komadai_piece_size / 8)
        mochigoma_heading_size = 4 * komadai_char_height # "▲\n持\n駒\n"
        
        c_hand = {ktype: count for (ktype, count) in hand.items() if count > 0}
        
        num_piece_types = len(c_hand)
        
        k_height = (
            mochigoma_heading_size + 2*komadai_char_height
            if num_piece_types == 0
            else mochigoma_heading_size
                 + num_piece_types*(symbol_size+pad)
                 - pad
        )
        if align == "bottom":
            # Adjust the "anchor" point
            y = y - k_height
        
        # Draw the komadai base
        rect = self.create_rectangle(
            x-komadai_piece_size, y,
            x+komadai_piece_size, y+k_height,
            fill=self.komadai_skin.colour,
            outline=""
        )
        
        header_text = "▲\n持\n駒" if sente else "△\n持\n駒"
        self.create_text(
            x, y,
            text=header_text,
            font=("", komadai_text_size),
            anchor="n"
        )
        if num_piece_types == 0:
            # Hand is empty, write なし
            self.create_text(
                x,
                y + mochigoma_heading_size,
                text="な\nし",
                font=("", komadai_text_size),
                anchor="n"
            )
            return rect
        else:
            # Hand is not empty
            for n, (ktype, count) in enumerate(c_hand.items()):
                if count == 0:
                    continue
                y_offset = (
                    mochigoma_heading_size
                    + n*(symbol_size+pad)
                    + symbol_size/2 # for the anchor="center"
                )
                self.draw_koma(
                    x-0.4*komadai_piece_size,
                    y+y_offset,
                    ktype = ktype,
                    komadai=True,
                    is_text=is_text,
                    anchor="center"
                )
                self.create_text(
                    x+0.5*komadai_piece_size,
                    y+y_offset,
                    text=str(count),
                    font=("", komadai_text_size),
                    anchor="center"
                )
        return rect
    
    def draw(self):
        """Draw complete board with komadai and pieces.
        """
        # Clear board display - could also keep board and just redraw pieces
        self.delete("all")
        position = self.position
        komadai_w = self.measurements.komadai_w
        coords_text_size = self.measurements.coords_text_size
        w_pad = self.measurements.w_pad
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        
        south_hand = position.hand_sente
        north_hand = position.hand_gote
        is_north_sente = self.is_upside_down
        
        if self.is_upside_down:
            north_hand, south_hand = south_hand, north_hand
        
        # Draw board
        self.draw_board()
        # Draw board pieces
        is_text = not self.piece_images.has_images()
        for koma, kset in position.koma_sets.items():
            ktype = KomaType.get(koma)
            side = koma.side()
            invert = (is_north_sente and (side == Side.SENTE)) or (not is_north_sente and (side == Side.GOTE))
            for idx in kset:
                col_num = position.idx_to_c(idx)
                row_num = position.idx_to_r(idx)
                x = col_num-1 if self.is_upside_down else 9-col_num
                y = 9-row_num if self.is_upside_down else row_num-1
                self.draw_koma(
                    x_sq(x+0.5), y_sq(y+0.5), ktype,
                    is_text=is_text, invert=invert
                )
        
        # Draw komadai
        self.north_komadai_rect = self.draw_komadai(
            w_pad + komadai_w/2,
            y_sq(0),
            north_hand,
            sente=is_north_sente,
            align="top"
        )
        self.south_komadai_rect = self.draw_komadai(
            x_sq(9) + 2*coords_text_size + komadai_w/2,
            y_sq(9),
            south_hand,
            sente=not is_north_sente,
            align="bottom"
        )
        return
    
    def apply_piece_skin(self, skin):
        self.piece_images.load(skin)
        return
    
    def apply_board_skin(self, skin):
        self.itemconfig(self.board_rect, fill=skin.colour)
        self.board_images.load(skin)
        board_img = (
            self.board_images.get_dict()["board"]
            if skin.path
            else ""
        )
        return
    
    def apply_komadai_skin(self, skin):
        # Can only figure out how to apply solid colours for now
        self.itemconfig(self.north_komadai_rect, fill=skin.colour)
        self.itemconfig(self.south_komadai_rect, fill=skin.colour)
        self.komadai_skin = skin
        return
    
    
    def on_resize(self, event):
        # Callback for when the canvas itself is resized
        self.measurements.recalculate_sizes(event.width, event.height)
        self.piece_images.resize_images()
        self.board_images.resize_images()
        # Redraw board after setting new dimensions
        self.draw()
        return
    
    def flip_board(self, want_upside_down):
        # For upside-down mode
        if self.is_upside_down != want_upside_down:
            self.is_upside_down = want_upside_down
            self.draw()
        return
