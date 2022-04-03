from __future__ import annotations

import functools
import tkinter as tk

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KanjiNumber, KomaType, Side, Square
from tsumemi.src.shogi.basetypes import HAND_TYPES, KANJI_FROM_KTYPE
from tsumemi.src.tsumemi.img_handlers import BoardImgManager, SkinSettings, BoardMeasurements, BoardSkin, KomaImgManager, KomadaiImgManager, PieceSkin

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Tuple
    from tsumemi.src.shogi.game import Game
    from tsumemi.src.shogi.position import Position
    from tsumemi.src.tsumemi.move_input_handler import MoveInputHandler


# Default/current canvas size for board
DEFAULT_CANVAS_WIDTH = 600
DEFAULT_CANVAS_HEIGHT = 500

# Shogi board dimensions in squares
NUM_COLS = 9
NUM_ROWS = 9

# IDX = zero-based, top left to bottom right, row-column (like FEN)
# NUM = one-based, top right to bottom left, column-row (like JP notation)


class BoardCanvas(tk.Canvas):
    """The canvas where the shogi position is drawn. Responsible for
    drawing on itself, delegating other tasks like size calculation to
    other objects.
    """
    def __init__(self, parent: tk.Widget, game: Game,
            skin_settings: SkinSettings,
            width: int = DEFAULT_CANVAS_WIDTH,
            height: int = DEFAULT_CANVAS_HEIGHT,
            *args, **kwargs
        ) -> None:
        """Initialise self with reference to a Game, allowing self to
        display board positions from the Game (purely a view).
        """
        self.width: int = width
        self.height: int = height
        self.is_upside_down: bool = False
        super().__init__(parent, width=width, height=height, *args, **kwargs)
        # Specify source of board data
        self.move_input_handler: Optional[MoveInputHandler] = None
        self.position: Position = game.position
        # Initialise measurements, used for many other things
        self.measurements = BoardMeasurements(width, height)
        # Load skins
        piece_skin, board_skin, komadai_skin = skin_settings.get()
        # Cached images and image settings
        self.koma_img_cache = KomaImgManager(self.measurements, piece_skin)
        self.board_img_cache = BoardImgManager(self.measurements, board_skin)
        self.komadai_img_cache = KomadaiImgManager(self.measurements, komadai_skin)
        # Images created and stored so only their image field changes later.
        # FEN ordering. (row_idx, col_idx), zero-based
        self.board_tiles = [[None] * NUM_COLS for i in range(NUM_ROWS)]
        self.board_select_tiles = [[None] * NUM_COLS for i in range(NUM_ROWS)]
        # Koma image IDs and their current positions
        self.koma_on_board_images: Dict[int, Tuple[int, int]] = {}
        # Currently highlighted tile [col_num, row_num]
        # Hand pieces would be [0, KomaType]
        self.highlighted_sq = Square.NONE
        self.highlighted_ktype = KomaType.NONE
        return
    
    def _col_idx_to_num(self, col_idx: int) -> int:
        return col_idx + 1 if self.is_upside_down else NUM_COLS - col_idx
    
    def _row_idx_to_num(self, row_idx: int) -> int:
        return NUM_ROWS - row_idx if self.is_upside_down else row_idx + 1
    
    def _col_num_to_idx(self, col_num: int) -> int:
        return col_num - 1 if self.is_upside_down else NUM_COLS - col_num
    
    def _row_num_to_idx(self, row_num: int) -> int:
        return NUM_ROWS - row_num if self.is_upside_down else row_num - 1
    
    def _idxs_to_xy(self, col_idx: int, row_idx: int, centering=""
        ) -> Tuple[int, int]:
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        x = x_sq(col_idx+0.5) if "x" in centering.lower() else x_sq(col_idx)
        y = y_sq(row_idx+0.5) if "y" in centering.lower() else y_sq(row_idx)
        return x, y
    
    def _is_inverted(self, side: Side) -> bool:
        return not (side.is_sente() ^ self.is_upside_down)
    
    def set_position(self, pos: Position) -> None:
        """Set the internal position (and of any associated input
        handler) to the given Position object.
        """
        self.position = pos
        if self.move_input_handler is not None:
            self.move_input_handler.position = pos
        self.draw()
        return
    
    def _unhighlight_square(self) -> None:
        if self.highlighted_sq == Square.NONE:
            return
        if self.highlighted_sq == Square.HAND:
            for id in self.find_withtag("komadai"):
                self.itemconfig(id, image="")
            return
        col_num, row_num = self.highlighted_sq.get_cr()
        col_idx = self._col_num_to_idx(col_num)
        row_idx = self._row_num_to_idx(row_num)
        img_idx = self.board_select_tiles[row_idx][col_idx]
        self.itemconfig(
            img_idx,
            image=self.board_img_cache.get_dict()["transparent"]
        )
        return
    
    def _highlight_square(self, sq: Square) -> None:
        if sq == Square.HAND:
            return
        if sq == Square.NONE:
            self.highlighted_sq = sq
            return
        col_num, row_num = sq.get_cr()
        col_idx = self._col_num_to_idx(col_num)
        row_idx = self._row_num_to_idx(row_num)
        img_idx = self.board_select_tiles[row_idx][col_idx]
        self.itemconfig(
            img_idx,
            image=self.board_img_cache.get_dict()["highlight"]
        )
        self.highlighted_sq = sq
        return
    
    def _highlight_hand_koma(self, ktype: KomaType) -> None:
        if ktype == KomaType.NONE:
            return
        side_str = "sente" if self.position.turn == Side.SENTE else "gote"
        ids_komadai = self.find_withtag("komadai")
        ids_ktype_csa = self.find_withtag(ktype.to_csa())
        ids_side = self.find_withtag(side_str)
        item = [
            id for id in ids_komadai
            if (id in ids_ktype_csa) and (id in ids_side)
        ]
        if item:
            self.itemconfig(item[0],
                image=self.komadai_img_cache.get_dict()["highlight"]
            )
        self.highlighted_sq = Square.HAND
        return
    
    def set_focus(self, sq: Square, ktype: KomaType=KomaType.NONE) -> None:
        self._unhighlight_square()
        if sq == Square.HAND:
            self._highlight_hand_koma(ktype)
        else:
            self._highlight_square(sq)
        return
    
    def prompt_promotion(self, sq: Square, ktype: KomaType) -> None:
        """Display the visual cues prompting user to choose promotion
        or non-promotion.
        """
        id_cover = self.create_image(
            *self._idxs_to_xy(0, 0),
            image=self.board_img_cache.get_dict("board")["semi-transparent"],
            anchor="nw",
            tags=("promotion_prompt",)
        )
        col_num, row_num = sq.get_cr()
        col_idx = self._col_num_to_idx(col_num)
        row_idx = self._row_num_to_idx(row_num)
        is_text = not self.koma_img_cache.has_images()
        invert = self._is_inverted(self.position.turn)
        
        id_promoted = self.draw_koma(
            *self._idxs_to_xy(col_idx, row_idx, centering="xy"),
            ktype.promote(),
            is_text=is_text, invert=invert,
            tags=("promotion_prompt",),
        )
        assert id_promoted is not None
        id_unpromoted = self.draw_koma(
            *self._idxs_to_xy(col_idx, row_idx+1, centering="xy"),
            ktype,
            is_text=is_text, invert=invert,
            tags=("promotion_prompt",),
        )
        assert id_unpromoted is not None
        callback = functools.partial(
            self._prompt_promotion_callback, sq=sq, ktype=ktype
        )
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
        if self.move_input_handler is not None:
            self.move_input_handler.execute_promotion_choice(
                is_promotion, sq=sq, ktype=ktype
            )
            self.clear_promotion_prompts()
        return
    
    def clear_promotion_prompts(self) -> None:
        self.delete("promotion_prompt")
        return
    
    def _draw_board_coordinates(self) -> None:
        coords_text_size = self.measurements.coords_text_size
        for row_idx in range(NUM_ROWS):
            row_num = self._row_idx_to_num(row_idx)
            row_label = " " + KanjiNumber(row_num).name
            self.create_text(
                *self._idxs_to_xy(NUM_COLS, row_idx, centering="y"),
                text=" " + row_label,
                font=("", coords_text_size),
                anchor="w",
            )
        for col_idx in range(9):
            col_num = self._col_idx_to_num(col_idx)
            self.create_text(
                *self._idxs_to_xy(col_idx, 0, centering="x"),
                text=str(col_num),
                font=("", coords_text_size),
                anchor="s",
            )
        return
    
    def draw_board(self):
        """Draw just the shogiban, without pieces. Komadai areas not
        included.
        """
        coords_text_size = self.measurements.coords_text_size
        # Draw board
        board_skin = self.board_img_cache.skin
        # Colour board with solid colour
        self.board_rect = self.create_rectangle(
            *self._idxs_to_xy(0, 0),
            *self._idxs_to_xy(NUM_COLS, NUM_ROWS),
            fill=board_skin.colour,
        )
        for row_idx in range(9):
            for col_idx in range(9):
                # Create board image layer
                id = self.create_image(
                    self._idxs_to_xy(col_idx, row_idx),
                    image="", anchor="nw",
                )
                self.board_tiles[row_idx][col_idx] = id
                # Create focus highlight layer
                id_focus = self.create_image(
                    self._idxs_to_xy(col_idx, row_idx),
                    image=self.board_img_cache.get_dict()["transparent"],
                    anchor="nw",
                )
                self.board_select_tiles[row_idx][col_idx] = id_focus
                # Add callbacks
                if self.move_input_handler is not None:
                    col_num = self._col_idx_to_num(col_idx)
                    row_num = self._row_idx_to_num(row_idx)
                    sq = Square.from_cr(col_num, row_num)
                    callback = functools.partial(
                        self.move_input_handler.receive_square, sq=sq
                    )
                    self.tag_bind(id_focus, "<Button-1>", callback)
        if self.board_img_cache.has_images():
            board_img = self.board_img_cache.get_dict()["board"]
            for row in self.board_tiles:
                for tile in row:
                    self.itemconfig(tile, image=board_img)
        for i in range(10):
            self.create_line(
                *self._idxs_to_xy(i, 0),
                *self._idxs_to_xy(i, NUM_ROWS),
                fill="black", width=1,
            )
            self.create_line(
                *self._idxs_to_xy(0, i),
                *self._idxs_to_xy(NUM_COLS, i),
                fill="black", width=1,
            )
        # Draw board coordinates
        self._draw_board_coordinates()
        return
    
    def _draw_koma_image(self,
            x: int, y: int, ktype: KomaType,
            komadai: bool = False, invert: bool = False,
            anchor: str = "center",
            tags: Tuple[str] = ("",)
        ) -> Optional[int]:
        id: int
        if ktype == KomaType.NONE:
            return None
        piece_dict = self.koma_img_cache.get_dict(
            invert=invert, komadai=komadai
        )
        img = piece_dict[ktype]
        id = self.create_image(
            x, y, image=img,
            anchor=anchor, tags=tags
        )
        return id
    
    def _draw_koma_text(self,
            x: int, y: int, ktype: KomaType,
            komadai: bool = False, invert: bool = False,
            anchor: str = "center",
            tags: Tuple[str] = ("",)
        ) -> Optional[int]:
        id: int
        if ktype == KomaType.NONE:
            return None
        text_size = (
            self.measurements.komadai_text_size
            if komadai
            else self.measurements.sq_text_size
        )
        id = self.create_text(
            x, y, text=str(KANJI_FROM_KTYPE[ktype]),
            font=("", text_size),
            angle=180 if invert else 0,
            anchor=anchor, tags=tags
        )
        return id
    
    def draw_koma(self,
            x: int, y: int, ktype: KomaType,
            komadai: bool = False, invert: bool = False,
            is_text: bool = True, anchor: str = "center",
            tags: Tuple[str] = ("",)
        ) -> Optional[int]:
        """Draw koma at specified location. Text is drawn if *is_text*
        is True; *anchor* determines how the image or text is
        positioned with respect to the point (x,y).
        """
        if is_text:
            return self._draw_koma_text(
                x, y, ktype, komadai, invert, anchor, tags
            )
        else:
            return self._draw_koma_image(
                x, y, ktype, komadai, invert, anchor, tags
            )
    
    def draw_komadai(self, x, y, hand, sente=True, align="top"):
        """Draw komadai with pieces given by hand argument, anchored
        at canvas position (x,y). "Anchoring" north or south achieved
        with align="top" or "bottom".
        """
        is_text = not self.koma_img_cache.has_images()
        # Komadai measurements.
        # Actual size of each character in px is about 1.5*text_size
        komadai_text_size = self.measurements.komadai_text_size
        komadai_char_height = 1.5 * komadai_text_size
        komadai_piece_size = self.measurements.komadai_piece_size
        symbol_size = komadai_text_size*3/2 if is_text else komadai_piece_size
        pad = (komadai_text_size / 8 if is_text else komadai_piece_size / 8)
        mochigoma_heading_size = 4 * komadai_char_height # "▲\n持\n駒\n"
        
        c_hand = {ktype: count for (ktype, count) in hand.mochigoma_dict.items() if count > 0}
        num_piece_types = len(c_hand)
        k_width = 2 * komadai_piece_size
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
        self.create_rectangle(
            x-(k_width/2), y,
            x+(k_width/2), y+k_height,
            fill=self.komadai_img_cache.skin.colour,
            outline="",
            tags=("komadai-solid",)
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
                x, y+mochigoma_heading_size,
                text="な\nし", font=("", komadai_text_size),
                anchor="n"
            )
            return
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
                id_highlight = self.create_image(
                    x-(k_width/5),
                    y+y_offset,
                    image="",
                    anchor="center",
                    tags=("komadai", ktype.to_csa(),
                        "sente" if sente else "gote"
                    )
                )
                id = self.draw_koma(
                    x-(k_width/5),
                    y+y_offset,
                    ktype=ktype,
                    komadai=True,
                    is_text=is_text,
                    anchor="center"
                )
                if self.move_input_handler is not None:
                    callback = functools.partial(
                        self.move_input_handler.receive_square,
                        sq=Square.HAND, hand_ktype=ktype,
                        hand_side = Side.SENTE if sente else Side.GOTE
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
        return
    
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
        
        if self.is_upside_down:
            north_hand, south_hand = south_hand, north_hand
        
        # Draw board
        self.draw_board()
        # Draw board pieces
        is_text = not self.koma_img_cache.has_images()
        for koma, kset in position.board.koma_sets.items():
            ktype = KomaType.get(koma)
            invert = self._is_inverted(koma.side())
            for idx in kset:
                col_num = position.board.idx_to_c(idx)
                row_num = position.board.idx_to_r(idx)
                col_idx = self._col_num_to_idx(col_num)
                row_idx = self._row_num_to_idx(row_num)
                id = self.draw_koma(
                    *self._idxs_to_xy(col_idx, row_idx, centering="xy"),
                    ktype,
                    is_text=is_text, invert=invert
                )
                self.koma_on_board_images[id] = (col_num, row_num)
                if self.move_input_handler is not None:
                    sq = Square.from_cr(col_num, row_num)
                    callback = functools.partial(
                        self.move_input_handler.receive_square, sq=sq
                    )
                    self.tag_bind(id, "<Button-1>", callback)
        
        # Draw komadai
        self.draw_komadai(
            w_pad + komadai_w/2,
            y_sq(0),
            north_hand,
            sente=self.is_upside_down,
            align="top"
        )
        self.draw_komadai(
            x_sq(9) + 2*coords_text_size + komadai_w/2,
            y_sq(9),
            south_hand,
            sente=not self.is_upside_down,
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
        return
    
    def apply_komadai_skin(self, skin: BoardSkin) -> None:
        # Can only figure out how to apply solid colours for now
        self.itemconfig("komadai-solid", fill=skin.colour)
        self.komadai_img_cache.load(skin)
        return
    
    
    def on_resize(self, event: tk.Event) -> None:
        # Callback for when the canvas itself is resized
        self.width = event.width
        self.height = event.height
        self.measurements.recalculate_sizes(event.width, event.height)
        self.koma_img_cache.resize_images()
        self.board_img_cache.resize_images()
        self.komadai_img_cache.resize_images()
        # Redraw board after setting new dimensions
        self.draw()
        return
    
    def flip_board(self, want_upside_down: bool) -> None:
        # For upside-down mode
        if self.is_upside_down != want_upside_down:
            self.is_upside_down = want_upside_down
            self.draw()
        return
