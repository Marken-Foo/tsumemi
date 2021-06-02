from __future__ import annotations

import functools
import tkinter as tk

from collections import Counter
from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KanjiNumber, Koma, KomaType, Side, Square, HAND_TYPES, KANJI_FROM_KTYPE
from tsumemi.src.tsumemi.img_handlers import BoardImgManager, BoardMeasurements, BoardSkin, KomaImgManager, PieceSkin

if TYPE_CHECKING:
    from typing import Dict, Optional, Tuple
    from tsumemi.src.tsumemi.model import GameAdapter


class BoardCanvas(tk.Canvas):
    """The canvas where the shogi position is drawn. Responsible for
    drawing on itself, delegating other tasks like size calculation to
    other objects.
    """
    # Default/current canvas size for board
    CANVAS_WIDTH = 600
    CANVAS_HEIGHT = 500
    
    def __init__(self, parent, controller, position, *args, **kwargs):
        self.controller = controller
        self.is_upside_down = False
        super().__init__(parent, *args, **kwargs)
        # Specify source of board data
        self.game_adapter: Optional[GameAdapter] = None
        self.position = position
        config = self.controller.config
        # Initialise measurements, used for many other things
        self.measurements = BoardMeasurements(
            self.CANVAS_WIDTH, self.CANVAS_HEIGHT
        )
        # Load skins
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
        # Cached images and image settings
        self.koma_img_cache = KomaImgManager(self.measurements, piece_skin)
        self.board_img_cache = BoardImgManager(self.measurements, board_skin)
        self.komadai_skin = komadai_skin
        # Images created and stored so only their image field changes later.
        # FEN ordering. (row_idx, col_idx), zero-based
        self.board_tiles = [[None] * 9 for i in range(9)]
        self.board_select_tiles = [[None] * 9 for i in range(9)]
        # Koma image IDs and their current positions
        self.koma_on_board_images: Dict[int, Tuple[int, int]] = {}
        # Currently highlighted tile [col_num, row_num]
        # Hand pieces would be [0, KomaType]
        self.highlighted_sq = Square.NONE
        return
    
    def connect_game_adapter(self, game_adapter: GameAdapter) -> None:
        self.game_adapter = game_adapter
        self.position = game_adapter.position
        return
    
    def set_focus(self, sq: Square) -> None:
        """Put visual focus on a particular square or koma.
        """
        if self.highlighted_sq != Square.NONE:
            col, row = self.highlighted_sq.get_cr()
            col_idx = col-1 if self.is_upside_down else 9-col
            row_idx = 9-row if self.is_upside_down else row-1
            old_idx = self.board_select_tiles[row_idx][col_idx]
            self.itemconfig(old_idx, image=self.board_img_cache.get_dict()["transparent"])
        if sq == Square.HAND:
            #TODO
            pass
        elif sq != Square.NONE:
            col_num, row_num = sq.get_cr()
            col_idx = col_num-1 if self.is_upside_down else 9-col_num
            row_idx = 9-row_num if self.is_upside_down else row_num-1
            img_idx = self.board_select_tiles[row_idx][col_idx]
            self.itemconfig(img_idx, image=self.board_img_cache.get_dict()["highlight"])
        self.highlighted_sq = sq
        return
    
    def prompt_promotion(self, sq: Square, ktype: KomaType) -> None:
        """Display the visual cues prompting user to choose promotion
        or non-promotion.
        """
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        id_cover = self.create_image(
            x_sq(0), y_sq(0),
            image=self.board_img_cache.get_dict("board")["semi-transparent"],
            anchor="nw",
            tag="promotion_prompt"
        )
        col_num, row_num = sq.get_cr()
        col_idx = col_num-1 if self.is_upside_down else 9-col_num
        row_idx = 9-row_num if self.is_upside_down else row_num-1
        is_text = not self.koma_img_cache.has_images()
        is_north_sente = self.is_upside_down
        side = self.position.turn
        invert = (is_north_sente and (side == Side.SENTE)) or (not is_north_sente and (side == Side.GOTE))
        id_promoted = self.draw_koma(
            x_sq(col_idx+0.5), y_sq(row_idx+0.5), ktype.promote(),
            is_text=is_text, invert=invert,
            tag="promotion_prompt"
        )
        id_unpromoted = self.draw_koma(
            x_sq(col_idx+0.5), y_sq(row_idx+0.5+1), ktype,
            is_text=is_text, invert=invert,
            tag="promotion_prompt"
        )
        callback = functools.partial(self._prompt_promotion_callback, sq=sq, ktype=ktype)
        self.tag_bind(id_promoted, "<Button-1>",
            functools.partial(callback, is_promotion=True)
        )
        self.tag_bind(id_unpromoted, "<Button-1>",
            functools.partial(callback, is_promotion=False)
        )
        self.tag_bind(id_cover, "<Button-1>",
            functools.partial(callback, is_promotion=None)
        )
        return
    
    def _prompt_promotion_callback(self, event,
                sq: Square, ktype: KomaType,
                is_promotion: Optional[bool]
            ) -> None:
        """Callback for promotion prompt. Clears the visual cues and
        passes the selected choice to underlying adapter. Use None
        for is_promotion to indicate cancellation of the move.
        """
        if self.game_adapter is not None:
            self.game_adapter.execute_promotion_choice(
                is_promotion, sq=sq, ktype=ktype
            )
            self.delete("promotion_prompt")
        return
    
    def draw_board(self):
        """Draw just the shogiban, without pieces. Komadai areas not
        included.
        """
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        coords_text_size = self.measurements.coords_text_size
        # Draw board
        board_skin = self.board_img_cache.skin
        # Colour board with solid colour
        self.board_rect = self.create_rectangle(
            x_sq(0), y_sq(0),
            x_sq(9), y_sq(9),
            fill=board_skin.colour
        )
        for row_idx in range(9):
            for col_idx in range(9):
                # Create board image layer
                id = self.create_image(
                    x_sq(col_idx), y_sq(row_idx),
                    image="", anchor="nw"
                )
                self.board_tiles[row_idx][col_idx] = id
                # Create focus highlight layer
                id_focus = self.create_image(
                    x_sq(col_idx), y_sq(row_idx),
                    image=self.board_img_cache.get_dict()["transparent"],
                    anchor="nw"
                )
                self.board_select_tiles[row_idx][col_idx] = id_focus
                # Add callbacks
                if self.game_adapter is not None:
                    col_num = col_idx+1 if self.is_upside_down else 9-col_idx
                    row_num = 9-row_idx if self.is_upside_down else row_idx+1
                    sq = Square.from_cr(col_num, row_num)
                    callback = functools.partial(self.game_adapter.receive_square, sq=sq)
                    self.tag_bind(id_focus, "<Button-1>", callback)
        if self.board_img_cache.has_images():
            board_img = self.board_img_cache.get_dict()["board"]
            for row in self.board_tiles:
                for tile in row:
                    self.itemconfig(tile, image=board_img)
        for i in range(10):
            self.create_line(x_sq(i), y_sq(0), x_sq(i), y_sq(9),
                                    fill="black", width=1)
            self.create_line(x_sq(0), y_sq(i), x_sq(9), y_sq(i),
                                    fill="black", width=1)
        # Draw board coordinates
        for row_idx in range(9):
            row_num = 9-row_idx if self.is_upside_down else row_idx+1
            row_label = " " + KanjiNumber(row_num).name
            self.create_text(
                x_sq(9), y_sq(row_idx+0.5),
                text=" " + row_label,
                font=("", coords_text_size),
                anchor="w"
            )
        for col_idx in range(9):
            col_num = col_idx+1 if self.is_upside_down else 9-col_idx
            self.create_text(
                x_sq(col_idx+0.5), y_sq(0),
                text=str(col_num),
                font=("", coords_text_size),
                anchor="s"
            )
        return
    
    def draw_koma(self,
            x: int, y: int, ktype: KomaType,
            komadai: bool = False, invert: bool = False,
            is_text: bool = True, anchor: str = "center",
            tag: str = ""
        ) -> Optional[int]:
        """Draw koma at specified location. Text is drawn if *is_text*
        is True; *anchor* determines how the image or text is
        positioned with respect to the point (x,y).
        """
        id: int
        if ktype == KomaType.NONE:
            return None
        if is_text:
            text_size = (
                self.measurements.komadai_text_size
                if komadai
                else self.measurements.sq_text_size
            )
            id = self.create_text(
                x, y, text=str(KANJI_FROM_KTYPE[ktype]),
                font=("", text_size),
                angle=180 if invert else 0,
                anchor=anchor, tag=tag
            )
        else:
            piece_dict = self.koma_img_cache.get_dict(
                invert=invert, komadai=komadai
            )
            img = piece_dict[ktype]
            id = self.create_image(
                x, y, image=img,
                anchor=anchor, tag=tag
            )
        return id
    
    def draw_komadai(self, x, y, hand, sente=True, align="top"):
        """Draw komadai with pieces given by hand argument, anchored
        at canvas position (x,y). "Anchoring" north or south achieved
        with align="top" or "bottom".
        """
        # Note: actual size of each character in px is about 1.5*text_size
        komadai_text_size = self.measurements.komadai_text_size
        komadai_char_height = 1.5 * komadai_text_size
        komadai_piece_size = self.measurements.komadai_piece_size
        is_text = not self.koma_img_cache.has_images()
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
                id = self.draw_koma(
                    x-0.4*komadai_piece_size,
                    y+y_offset,
                    ktype=ktype,
                    komadai=True,
                    is_text=is_text,
                    anchor="center"
                )
                if self.game_adapter is not None:
                    callback = functools.partial(
                        self.game_adapter.receive_square,
                        sq=Square.HAND, hand_ktype=ktype
                    )
                    self.tag_bind(id, "<Button-1>", callback)
                #TODO: register drawn piece image with self.[some dict]
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
        is_text = not self.koma_img_cache.has_images()
        for koma, kset in position.koma_sets.items():
            ktype = KomaType.get(koma)
            side = koma.side()
            invert = (is_north_sente and (side == Side.SENTE)) or (not is_north_sente and (side == Side.GOTE))
            for idx in kset:
                col_num = position.idx_to_c(idx)
                row_num = position.idx_to_r(idx)
                x = col_num-1 if self.is_upside_down else 9-col_num
                y = 9-row_num if self.is_upside_down else row_num-1
                id = self.draw_koma(
                    x_sq(x+0.5), y_sq(y+0.5), ktype,
                    is_text=is_text, invert=invert
                )
                self.koma_on_board_images[id] = (col_num, row_num)
                if self.game_adapter is not None:
                    sq = Square.from_cr(col_num, row_num)
                    callback = functools.partial(
                        self.game_adapter.receive_square, sq=sq
                    )
                    self.tag_bind(id, "<Button-1>", callback)
        
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
        # set focus
        self.set_focus(self.highlighted_sq)
        return
    
    def apply_piece_skin(self, skin: PieceSkin) -> None:
        self.koma_img_cache.load(skin)
        return
    
    def apply_board_skin(self, skin: BoardSkin) -> None:
        self.itemconfig(self.board_rect, fill=skin.colour)
        self.board_img_cache.load(skin)
        board_img = (
            self.board_img_cache.get_dict()["board"]
            if skin.path
            else ""
        )
        return
    
    def apply_komadai_skin(self, skin: BoardSkin) -> None:
        # Can only figure out how to apply solid colours for now
        self.itemconfig(self.north_komadai_rect, fill=skin.colour)
        self.itemconfig(self.south_komadai_rect, fill=skin.colour)
        self.komadai_skin = skin
        return
    
    
    def on_resize(self, event):
        # Callback for when the canvas itself is resized
        self.measurements.recalculate_sizes(event.width, event.height)
        self.koma_img_cache.resize_images()
        self.board_img_cache.resize_images()
        # Redraw board after setting new dimensions
        self.draw()
        return
    
    def flip_board(self, want_upside_down: bool) -> None:
        # For upside-down mode
        if self.is_upside_down != want_upside_down:
            self.is_upside_down = want_upside_down
            self.draw()
        return
