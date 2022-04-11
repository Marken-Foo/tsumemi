from __future__ import annotations

import functools
import tkinter as tk

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KomaType, Side, Square
from tsumemi.src.shogi.basetypes import HAND_TYPES
from tsumemi.src.tsumemi.board_artist import BoardArtist, NUM_COLS, NUM_ROWS
from tsumemi.src.tsumemi.img_handlers import BoardImgManager, SkinSettings, BoardMeasurements, BoardSkin, KomaImgManager, KomadaiImgManager, PieceSkin
from tsumemi.src.tsumemi.koma_artist import ImageKomaArtist, TextKomaArtist
from tsumemi.src.tsumemi.komadai_artist import KomadaiArtist

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from tsumemi.src.shogi.game import Game
    from tsumemi.src.shogi.position import Position
    from tsumemi.src.tsumemi.koma_artist import AbstractKomaArtist
    from tsumemi.src.tsumemi.move_input_handler import MoveInputHandler


# Default/current canvas size for board
DEFAULT_CANVAS_WIDTH = 600
DEFAULT_CANVAS_HEIGHT = 500


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
        self.board_artist = BoardArtist()
        # Currently highlighted tile [col_num, row_num]
        # Hand pieces would be [0, KomaType]
        self.highlighted_sq = Square.NONE
        self.highlighted_ktype = KomaType.NONE
        return

    def col_idx_to_num(self, col_idx: int) -> int:
        return col_idx + 1 if self.is_upside_down else NUM_COLS - col_idx

    def row_idx_to_num(self, row_idx: int) -> int:
        return NUM_ROWS - row_idx if self.is_upside_down else row_idx + 1

    def _col_num_to_idx(self, col_num: int) -> int:
        return col_num - 1 if self.is_upside_down else NUM_COLS - col_num

    def _row_num_to_idx(self, row_num: int) -> int:
        return NUM_ROWS - row_num if self.is_upside_down else row_num - 1

    def _sq_to_idxs(self, sq: Square) -> Tuple[int, int]:
        col_num, row_num = sq.get_cr()
        col_idx = self._col_num_to_idx(col_num)
        row_idx = self._row_num_to_idx(row_num)
        return col_idx, row_idx

    def idxs_to_xy(self, col_idx: int, row_idx: int, centering=""
        ) -> Tuple[int, int]:
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        x = x_sq(col_idx+0.5) if "x" in centering.lower() else x_sq(col_idx)
        y = y_sq(row_idx+0.5) if "y" in centering.lower() else y_sq(row_idx)
        return x, y

    def make_koma_artist(self, invert: bool, komadai: bool
        ) -> AbstractKomaArtist:
        if self.is_text():
            return TextKomaArtist(canvas=self, invert=invert, komadai=komadai)
        else:
            koma_dict = self.koma_img_cache.get_dict(
                invert=invert, komadai=komadai
            )
            return ImageKomaArtist(koma_dict)

    def _is_inverted(self, side: Side) -> bool:
        return not (side.is_sente() ^ self.is_upside_down)

    def is_text(self) -> bool:
        return not self.koma_img_cache.has_images()

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
            for id_ in self.find_withtag("komadai_focus"):
                self.itemconfig(id_, image="")
            return
        col_idx, row_idx = self._sq_to_idxs(self.highlighted_sq)
        self.board_artist.unhighlight_square(self, row_idx, col_idx)
        return

    def _highlight_square(self, sq: Square) -> None:
        if sq == Square.HAND:
            return
        if sq == Square.NONE:
            self.highlighted_sq = sq
            return
        col_idx, row_idx = self._sq_to_idxs(sq)
        self.board_artist.highlight_square(self, row_idx, col_idx)
        self.highlighted_sq = sq
        return

    def _highlight_hand_koma(self, ktype: KomaType) -> None:
        if ktype == KomaType.NONE:
            return
        side_str = "sente" if self.position.turn == Side.SENTE else "gote"
        item = self.find_withtag(
            f"komadai_focus&&{ktype.to_csa()}&&{side_str}"
        )
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
            *self.idxs_to_xy(0, 0),
            image=self.board_img_cache.get_dict("board")["semi-transparent"],
            anchor="nw",
            tags=("promotion_prompt",)
        )
        col_idx, row_idx = self._sq_to_idxs(sq)
        invert = self._is_inverted(self.position.turn)

        id_promoted = self.draw_koma(
            *self.idxs_to_xy(col_idx, row_idx, centering="xy"),
            ktype.promote(),
            invert=invert,
            tags=("promotion_prompt",),
        )
        assert id_promoted is not None
        id_unpromoted = self.draw_koma(
            *self.idxs_to_xy(col_idx, row_idx+1, centering="xy"),
            ktype,
            invert=invert,
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

    def _prompt_promotion_callback(self, event: tk.Event,
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

    def _draw_canvas_base_layer(self) -> int:
        id_: int = self.create_rectangle(
            0, 0, self.width, self.height, fill="#ffffff"
        )
        return id_

    def _add_board_onclick_callbacks(self) -> None:
        if self.move_input_handler is None:
            return
        for row_idx in range(NUM_ROWS):
            for col_idx in range(NUM_COLS):
                col_num = self.col_idx_to_num(col_idx)
                row_num = self.row_idx_to_num(row_idx)
                sq = Square.from_cr(col_num, row_num)
                callback = functools.partial(
                    self.move_input_handler.receive_square, sq=sq
                )
                self.tag_bind(
                    self.board_artist.board_select_tiles[row_idx][col_idx],
                    "<Button-1>",
                    callback,
                )
        return

    def _update_board_tile_images(self) -> None:
        if not self.board_img_cache.has_images():
            return
        board_img = self.board_img_cache.get_dict()["board"]
        self.board_artist.update_board_tile_images(self, board_img)
        return

    def draw_board(self):
        """Draw just the shogiban, without pieces. Komadai areas not
        included.
        """
        self._draw_canvas_base_layer()
        artist = self.board_artist
        artist.draw_board_base_layer(self)
        artist.draw_board_tile_layer(self)
        artist.draw_board_focus_layer(self)
        artist.draw_board_grid_lines(self)
        artist.draw_board_coordinates(self)

        board_skin = self.board_img_cache.skin
        self.itemconfig(self.board_artist.board_rect, fill=board_skin.colour)
        self._add_board_onclick_callbacks()
        self._update_board_tile_images()
        return

    def draw_koma(self,
            x: int, y: int, ktype: KomaType,
            invert: bool = False,
            anchor: str = "center",
            tags: Tuple[str] = ("",),
        ) -> Optional[int]:
        """Draw koma at specified location. *anchor* determines how the image
        or text is positioned with respect to the point (x,y).
        """
        artist = self.make_koma_artist(invert, False)
        return artist.draw_koma(self, x, y, ktype, anchor, tags)

    def _add_all_komadai_koma_onclick_callbacks(self) -> None:
        if self.move_input_handler is None:
            return
        for side in (Side.SENTE, Side.GOTE):
            side_str = "sente" if side.is_sente() else "gote"
            for ktype in HAND_TYPES:
                callback = functools.partial(
                    self.move_input_handler.receive_square,
                    sq=Square.HAND, hand_ktype=ktype,
                    hand_side=side,
                )
                ids = self.find_withtag(
                    f"komadai_koma&&{ktype.to_csa()}&&{side_str}"
                )
                for id_ in ids:
                    self.tag_bind(id_, "<Button-1>", callback)
        return

    def draw_komadai(self, x, y, hand, sente=True, align="top"):
        """Draw komadai with pieces given by hand argument, anchored
        at canvas position (x,y). "Anchoring" north or south achieved
        with align="top" or "bottom".
        """
        artist = KomadaiArtist(x, y, self, hand, sente, align)
        # Draw the komadai base
        komadai_base = artist.draw_komadai_base(self)
        self.itemconfig(komadai_base, fill=self.komadai_img_cache.skin.colour)
        artist.draw_komadai_header_text(self)
        artist.draw_all_komadai_koma(self)
        self._add_all_komadai_koma_onclick_callbacks()
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

        north_side = (
            Side.SENTE if self._is_inverted(Side.SENTE) else Side.GOTE
        )
        south_side = north_side.switch()
        north_hand = position.get_hand_of_side(north_side)
        south_hand = position.get_hand_of_side(south_side)

        # Draw board
        self.draw_board()
        # Draw board pieces
        for koma, sqset in position.get_koma_sets().items():
            for sq in sqset:
                col_idx, row_idx = self._sq_to_idxs(sq)
                id_ = self.draw_koma(
                    *self.idxs_to_xy(col_idx, row_idx, centering="xy"),
                    ktype=KomaType.get(koma),
                    invert=self._is_inverted(koma.side()),
                )
                if self.move_input_handler is not None:
                    callback = functools.partial(
                        self.move_input_handler.receive_square, sq=sq
                    )
                    self.tag_bind(id_, "<Button-1>", callback)

        # Draw komadai
        self.draw_komadai(
            w_pad + komadai_w/2,
            y_sq(0),
            north_hand,
            sente=north_side.is_sente(),
            align="top"
        )
        self.draw_komadai(
            x_sq(9) + 2*coords_text_size + komadai_w/2,
            y_sq(9),
            south_hand,
            sente=south_side.is_sente(),
            align="bottom"
        )
        # set focus
        self.set_focus(self.highlighted_sq)
        return

    def apply_piece_skin(self, skin: PieceSkin) -> None:
        self.koma_img_cache.load(skin)
        return

    def apply_board_skin(self, skin: BoardSkin) -> None:
        self.itemconfig(self.board_artist.board_rect, fill=skin.colour)
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
