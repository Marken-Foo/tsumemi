from __future__ import annotations

import functools
import tkinter as tk

from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.board_gui.koma_image_cache import KomaImageCache
import tsumemi.src.tsumemi.event as evt

from tsumemi.src.shogi.basetypes import HAND_TYPES, KANJI_FROM_KTYPE, KomaType, Side
from tsumemi.src.shogi.square import Square
from tsumemi.src.tsumemi.skins import BoardSkin, PieceSkin, SkinSettings
from tsumemi.src.tsumemi.board_gui.board_artist import BoardArtist, NUM_COLS, NUM_ROWS
from tsumemi.src.tsumemi.board_gui.board_meas import BoardMeasurements
from tsumemi.src.tsumemi.board_gui.img_handlers import KomadaiImgManager
from tsumemi.src.tsumemi.board_gui.komadai_artist import KomadaiArtist

if TYPE_CHECKING:
    from typing import Any
    from tsumemi.src.shogi.position import Position
    from tsumemi.src.shogi.position_internals import HandRepresentation
    from tsumemi.src.tsumemi.game.game_model import GameStepEvent, GameUpdateEvent
    from tsumemi.src.tsumemi.move_input_handler import MoveInputHandler


# Default/current canvas size for board
DEFAULT_CANVAS_WIDTH = 600
DEFAULT_CANVAS_HEIGHT = 500

# tk input
TK_SINGLE_LEFT_CLICK = "<Button-1>"


# IDX = zero-based, top left to bottom right, row-column (like FEN)
# NUM = one-based, top right to bottom left, column-row (like JP notation)


class BoardCanvas(tk.Canvas, evt.IObserver):
    """The canvas where the shogi position is drawn. Responsible for
    drawing on itself, delegating other tasks like size calculation to
    other objects.
    """

    def __init__(
        self,
        parent: tk.Widget,
        position: Position,
        skin_settings: SkinSettings,
        *args: Any,
        width: int = DEFAULT_CANVAS_WIDTH,
        height: int = DEFAULT_CANVAS_HEIGHT,
        **kwargs: Any,
    ) -> None:
        """Initialise self with reference to a Game, allowing self to
        display board positions from the Game (purely a view).
        """
        self.width: int = width
        self.height: int = height
        self.is_upside_down: bool = False
        tk.Canvas.__init__(self, parent, width=width, height=height, *args, **kwargs)
        evt.IObserver.__init__(self)
        # Specify source of board data
        self.move_input_handler: MoveInputHandler | None = None
        self.position: Position = position
        # Initialise measurements, used for many other things
        self.measurements = BoardMeasurements(width, height)
        # Load skins
        piece_skin, board_skin, komadai_skin = skin_settings.get()
        # Cached images and image settings
        self.koma_image_cache = KomaImageCache(
            self.measurements.sq_w, self.measurements.sq_h, piece_skin
        )
        self.komadai_koma_image_cache = KomaImageCache(
            self.measurements.komadai_piece_size,
            self.measurements.komadai_piece_size,
            piece_skin,
        )
        self.komadai_img_cache = KomadaiImgManager(self.measurements, komadai_skin)
        self.board_artist = BoardArtist(self.measurements, board_skin)
        # Currently highlighted tile [col_num, row_num]
        # Hand pieces would be [0, KomaType]
        self.highlighted_sq = Square.NONE
        self.highlighted_ktype = KomaType.NONE
        # Last move highlighted tiles
        self.last_move_start_sq = Square.NONE
        self.last_move_end_sq = Square.NONE

    def set_and_draw_callback(self, event: GameStepEvent | GameUpdateEvent) -> None:
        last_move = event.game.get_last_move()
        self.last_move_start_sq = last_move.start_sq
        self.last_move_end_sq = last_move.end_sq
        self.set_position(event.game.get_position())

    def set_position(self, pos: Position) -> None:
        """Set the internal position (and of any associated input
        handler) to the given Position object.
        """
        self.position = pos
        if self.move_input_handler is not None:
            self.move_input_handler.position = pos
        self.draw()

    def apply_piece_skin(self, skin: PieceSkin) -> None:
        self.koma_image_cache.update_skin(skin)
        self.komadai_koma_image_cache.update_skin(skin)

    def apply_board_skin(self, skin: BoardSkin) -> None:
        self.board_artist.apply_skin(self, skin)

    def apply_komadai_skin(self, skin: BoardSkin) -> None:
        # Can only figure out how to apply solid colours for now
        self.itemconfig("komadai-solid", fill=skin.colour)
        self.komadai_img_cache.load(skin)

    def on_resize(self, event: tk.Event) -> None:
        # Callback for when the canvas itself is resized
        self.width = event.width
        self.height = event.height
        self.measurements.recalculate_sizes(event.width, event.height)
        self.koma_image_cache.update_dimensions(
            self.measurements.sq_w, self.measurements.sq_h
        )
        self.komadai_koma_image_cache.update_dimensions(
            self.measurements.komadai_piece_size, self.measurements.komadai_piece_size
        )
        self.board_artist.update_measurements(
            self.measurements.sq_w, self.measurements.sq_h
        )
        self.komadai_img_cache.resize_images()
        # Redraw board after setting new dimensions
        self.draw()

    def flip_board(self, want_upside_down: bool) -> None:
        # For upside-down mode
        if self.is_upside_down != want_upside_down:
            self.is_upside_down = want_upside_down
            self.draw()

    def set_focus(self, sq: Square, ktype: KomaType = KomaType.NONE) -> None:
        self._unhighlight_square()
        if sq == Square.HAND:
            self._highlight_hand_koma(ktype)
        else:
            self._highlight_square(sq)
        # Kludge fix for _unhighlight_square() unhighlighting last move
        self._highlight_last_move()

    def draw(self) -> None:
        """Draw complete board with komadai and pieces."""
        # Clear board display - could also keep board and just redraw pieces
        self.delete("all")
        position = self.position
        komadai_w = self.measurements.komadai_w
        coords_text_size = self.measurements.coords_text_size
        w_pad = self.measurements.w_pad
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq

        north_side = Side.SENTE if self._is_inverted(Side.SENTE) else Side.GOTE
        south_side = north_side.switch()
        north_hand = position.get_hand_of_side(north_side)
        south_hand = position.get_hand_of_side(south_side)

        self._draw_canvas_base_layer()
        # Draw board
        self.board_artist.draw_board(self)
        self._add_board_onclick_callbacks()
        # Draw board pieces
        for koma, sqset in position.get_koma_sets().items():
            for sq in sqset:
                col_idx, row_idx = self._sq_to_idxs(sq)
                ktype = KomaType.get(koma)
                invert = self._is_inverted(koma.side())
                if self.is_text():
                    text = str(KANJI_FROM_KTYPE[ktype])
                    self.board_artist.draw_text_koma(
                        self, text, invert, row_idx, col_idx
                    )
                else:
                    img = self.koma_image_cache.get_koma_image(ktype, invert)
                    if img is None:
                        continue
                    self.board_artist.draw_koma(self, img, row_idx, col_idx)

        # Draw komadai
        self.draw_komadai(
            w_pad + komadai_w / 2,
            y_sq(0),
            north_hand,
            sente=north_side.is_sente(),
            align="top",
        )
        self.draw_komadai(
            x_sq(9) + 2 * coords_text_size + komadai_w / 2,
            y_sq(9),
            south_hand,
            sente=south_side.is_sente(),
            align="bottom",
        )
        # set focus and highlights
        self.set_focus(self.highlighted_sq)
        self.board_artist.lift_click_layer(self)
        self._highlight_last_move()

    def _draw_canvas_base_layer(self) -> int:
        id_: int = self.create_rectangle(0, 0, self.width, self.height, fill="#ffffff")
        return id_

    def draw_komadai(
        self,
        x: float,
        y: float,
        hand: HandRepresentation,
        sente: bool = True,
        align: str = "top",
    ) -> None:
        """Draw komadai with pieces given by hand argument, anchored
        at canvas position (x,y). "Anchoring" north or south achieved
        with align="top" or "bottom".
        """
        artist = KomadaiArtist(x, y, self, hand, sente, align)
        # Draw the komadai base
        komadai_base = artist.draw_komadai_base(self)
        skin = self.komadai_img_cache.skin
        assert isinstance(skin, BoardSkin)
        self.itemconfig(komadai_base, fill=skin.colour)
        artist.draw_komadai_header_text(self)
        artist.draw_all_komadai_koma(self)
        self._add_all_komadai_koma_onclick_callbacks()

    def prompt_promotion(self, sq: Square, ktype: KomaType) -> None:
        """Display the visual cues prompting user to choose promotion
        or non-promotion.
        """
        id_cover = self.board_artist.draw_promotion_cover(self)

        col_idx, row_idx = self._sq_to_idxs(sq)
        invert = self._is_inverted(self.position.turn)

        id_promoted = self._draw_promotion_prompt_koma(
            row_idx, col_idx, ktype.promote(), invert
        )
        id_unpromoted = self._draw_promotion_prompt_koma(
            row_idx + 1, col_idx, ktype, invert
        )
        callback = functools.partial(
            self._prompt_promotion_callback, sq=sq, ktype=ktype
        )
        if id_promoted is not None:
            self.tag_bind(
                id_promoted,
                TK_SINGLE_LEFT_CLICK,
                functools.partial(callback, is_promotion=True),
            )
        if id_unpromoted is not None:
            self.tag_bind(
                id_unpromoted,
                TK_SINGLE_LEFT_CLICK,
                functools.partial(callback, is_promotion=False),
            )
        if id_cover is not None:
            self.tag_bind(
                id_cover,
                TK_SINGLE_LEFT_CLICK,
                functools.partial(callback, is_promotion=None),
            )

    def _prompt_promotion_callback(
        self,
        _event: tk.Event,
        sq: Square,
        ktype: KomaType,
        is_promotion: bool | None,
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

    def clear_promotion_prompts(self) -> None:
        self.board_artist.clear_promotion_prompts(self)

    def col_idx_to_num(self, col_idx: int) -> int:
        return col_idx + 1 if self.is_upside_down else NUM_COLS - col_idx

    def row_idx_to_num(self, row_idx: int) -> int:
        return NUM_ROWS - row_idx if self.is_upside_down else row_idx + 1

    def _col_num_to_idx(self, col_num: int) -> int:
        return col_num - 1 if self.is_upside_down else NUM_COLS - col_num

    def _row_num_to_idx(self, row_num: int) -> int:
        return NUM_ROWS - row_num if self.is_upside_down else row_num - 1

    def _sq_to_idxs(self, sq: Square) -> tuple[int, int]:
        col_num, row_num = sq.get_cr()
        col_idx = self._col_num_to_idx(col_num)
        row_idx = self._row_num_to_idx(row_num)
        return col_idx, row_idx

    def idxs_to_xy(
        self, col_idx: int, row_idx: int, centering: str = ""
    ) -> tuple[int, int]:
        x_sq = self.measurements.x_sq
        y_sq = self.measurements.y_sq
        x = x_sq(col_idx + 0.5) if "x" in centering.lower() else x_sq(col_idx)
        y = y_sq(row_idx + 0.5) if "y" in centering.lower() else y_sq(row_idx)
        return int(x), int(y)

    def _draw_promotion_prompt_koma(
        self, row_idx: int, col_idx: int, ktype: KomaType, is_upside_down: bool
    ) -> int | None:
        if ktype == KomaType.NONE:
            return None
        img = self.koma_image_cache.get_koma_image(ktype, is_upside_down=is_upside_down)
        return self.create_image(  # type: ignore (tk typing issue)
            *self.idxs_to_xy(col_idx, row_idx, centering="xy"),
            image=img,
            anchor="center",
            tags=("promotion_prompt",),
        )

    def _is_inverted(self, side: Side) -> bool:
        return not (side.is_sente() ^ self.is_upside_down)

    def is_text(self) -> bool:
        return self.koma_image_cache.skin == PieceSkin.TEXT

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
                    self.board_artist.click_layer.tiles[row_idx][col_idx],
                    TK_SINGLE_LEFT_CLICK,
                    callback,
                )

    def _add_all_komadai_koma_onclick_callbacks(self) -> None:
        if self.move_input_handler is None:
            return
        for side in (Side.SENTE, Side.GOTE):
            side_str = "sente" if side.is_sente() else "gote"
            for ktype in HAND_TYPES:
                callback = functools.partial(
                    self.move_input_handler.receive_square,
                    sq=Square.HAND,
                    hand_ktype=ktype,
                    hand_side=side,
                )
                ids = self.find_withtag(f"komadai_koma&&{ktype.to_csa()}&&{side_str}")
                for id_ in ids:
                    self.tag_bind(id_, TK_SINGLE_LEFT_CLICK, callback)

    def _unhighlight_square(self) -> None:
        if self.highlighted_sq == Square.NONE:
            return
        if self.highlighted_sq == Square.HAND:
            for id_ in self.find_withtag("komadai_focus"):
                self.itemconfig(id_, image="")
            return
        col_idx, row_idx = self._sq_to_idxs(self.highlighted_sq)
        self.board_artist.unhighlight_square(self, row_idx, col_idx)

    def _highlight_square(self, sq: Square) -> None:
        if sq == Square.HAND:
            return
        if sq == Square.NONE:
            self.highlighted_sq = sq
            return
        col_idx, row_idx = self._sq_to_idxs(sq)
        self.board_artist.highlight_square(self, row_idx, col_idx)
        self.highlighted_sq = sq

    def _highlight_hand_koma(self, ktype: KomaType) -> None:
        if ktype == KomaType.NONE:
            return
        side_str = "sente" if self.position.turn == Side.SENTE else "gote"
        item = self.find_withtag(f"komadai_focus&&{ktype.to_csa()}&&{side_str}")
        if item:
            highlight_image = self.komadai_koma_image_cache.get_highlight_image()
            if highlight_image is None:
                self.highlighted_sq = Square.HAND
                return
            self.itemconfig(item[0], image=highlight_image)
        self.highlighted_sq = Square.HAND

    def _highlight_last_move_square(self, sq: Square) -> None:
        if sq == Square.HAND:
            return
        if sq == Square.NONE:
            return
        col_idx, row_idx = self._sq_to_idxs(sq)
        self.board_artist.highlight_square_2(self, row_idx, col_idx)

    def _highlight_last_move(self) -> None:
        self._highlight_last_move_square(self.last_move_start_sq)
        self._highlight_last_move_square(self.last_move_end_sq)
