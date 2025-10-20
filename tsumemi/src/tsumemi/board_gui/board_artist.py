from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KANJI_FROM_KTYPE, KomaType
from tsumemi.src.shogi.square import KanjiNumber, Square
from tsumemi.src.tsumemi.board_gui.board_image_cache import BoardImageCache
from tsumemi.src.tsumemi.board_gui.board_meas import BoardMeasurements

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import Literal
    from PIL import ImageTk
    from tsumemi.src.shogi.basetypes import Koma
    from tsumemi.src.tsumemi.board_gui.board_canvas import BoardCanvas
    from tsumemi.src.tsumemi.skins import BoardSkin


# Shogi board dimensions in squares
NUM_COLS = 9
NUM_ROWS = 9

# IDX = zero-based, top left to bottom right, row-column (like FEN)
# NUM = one-based, top right to bottom left, column-row (like JP notation)


class BoardArtist:
    def __init__(
        self, measurements: BoardMeasurements, skin: BoardSkin, is_upside_down: bool
    ) -> None:
        self.is_upside_down = is_upside_down

        self.background_id: int | None = None
        self.tile_backgrounds = BoardImageLayer()
        self.tile_highlights = BoardImageLayer()
        self.tile_images = BoardImageLayer(is_centered=True)
        self.tile_texts = TileIdStore(NUM_COLS, NUM_ROWS)
        self.tile_clickboxes = BoardImageLayer()

        self.board_image_cache = BoardImageCache(
            measurements.sq_w, measurements.sq_h, skin
        )
        self._drawing_coords = BoardDrawingCoords(
            measurements.sq_w, measurements.sq_h, measurements.get_board_top_left_xy()
        )

    def draw_board(self, canvas: BoardCanvas) -> None:
        self.background_id = self._create_base_layer(canvas)
        self._create_tile_background_layer(canvas)
        self._create_highlight_layer(canvas)
        self._create_koma_text_layer(canvas)
        self._create_koma_layer(canvas)
        self._create_grid_lines(canvas)
        self._create_notation_labels(canvas)
        self._create_clickbox_layer(canvas)

        self._update_base_layer(canvas, self.board_image_cache.skin)
        if not self.board_image_cache.skin.path:
            return

        tile_image = self.board_image_cache.get_board_image()
        if tile_image is not None:
            self._update_tile_backgrounds(canvas, tile_image)

    def flip(self) -> None:
        self.is_upside_down = not self.is_upside_down

    def _clear_komas(self, canvas: BoardCanvas) -> None:
        for _, id_ in self.tile_texts:
            if id_ is not None:
                canvas.itemconfig(id_, text="")
        self.tile_images.update_all_tiles(canvas, "")

    def draw(self, canvas: BoardCanvas, komas_by_square: dict[Square, Koma]) -> None:
        self._clear_komas(canvas)
        for sq, koma in komas_by_square.items():
            col_idx, row_idx = self.sq_to_idxs(sq)
            ktype = KomaType.get(koma)
            invert = canvas.is_inverted(koma.side())
            if canvas.is_text():
                self.display_text_koma(canvas, ktype, invert, row_idx, col_idx)
            else:
                self.display_koma(canvas, ktype, invert, row_idx, col_idx)

    def apply_board_skin(self, canvas: BoardCanvas, skin: BoardSkin) -> None:
        if self.background_id is not None:
            canvas.itemconfig(self.background_id, fill=skin.colour)
        self.board_image_cache.update_skin(skin)
        self._update_base_layer(canvas, skin)

    def update_measurements(
        self, sq_width: float, sq_height: float, board_top_left_xy: tuple[float, float]
    ) -> None:
        self.board_image_cache.update_dimensions(sq_width, sq_height)
        self._drawing_coords.update_coords(
            sq_width=sq_width,
            sq_height=sq_height,
            board_top_left_xy=board_top_left_xy,
        )

    def display_koma(
        self,
        canvas: BoardCanvas,
        ktype: KomaType,
        is_upside_down: bool,
        row_idx: int,
        col_idx: int,
    ) -> None:
        img = canvas.koma_image_cache.get_koma_image(
            ktype, is_upside_down=is_upside_down
        )
        id_ = self.tile_images.get_id(row_idx, col_idx)
        if id_ is not None and img is not None:
            canvas.itemconfig(id_, image=img)

    def display_text_koma(
        self,
        canvas: BoardCanvas,
        ktype: KomaType,
        is_upside_down: bool,
        row_idx: int,
        col_idx: int,
    ) -> None:
        id_ = self.tile_texts.get_id(row_idx=row_idx, col_idx=col_idx)
        if id_ is not None:
            text = str(KANJI_FROM_KTYPE[ktype])
            canvas.itemconfig(id_, text=text, angle=180 if is_upside_down else 0)

    def lift_click_layer(self, canvas: BoardCanvas) -> None:
        canvas.lift("click_tile")

    def draw_promotion_interface(
        self,
        canvas: BoardCanvas,
        ktype: KomaType,
        promotion_square: Square,
        is_upside_down: bool,
    ) -> tuple[int | None, int | None, int | None]:
        """
        Display on a `canvas` the interface for user to choose whether to promote a koma.
        Return the tkinter canvas IDs of the board covering, promoted koma, and unpromoted koma.
        """
        id_cover = self._draw_promotion_cover(canvas)
        col_idx, row_idx = self.sq_to_idxs(promotion_square)
        id_promoted = self._draw_promotion_prompt_koma(
            canvas, row_idx, col_idx, ktype.promote(), is_upside_down
        )
        id_unpromoted = self._draw_promotion_prompt_koma(
            canvas, row_idx + 1, col_idx, ktype, is_upside_down
        )
        return (id_cover, id_promoted, id_unpromoted)

    def _draw_promotion_cover(self, canvas: BoardCanvas) -> int | None:
        img = self.board_image_cache.get_semi_transparent_board_cover()
        if img is None:
            return None
        x, y = self._drawing_coords.idxs_to_xy(0, 0)
        return canvas.create_image(
            x, y, image=img, anchor="nw", tags="promotion_prompt"
        )

    def _draw_promotion_prompt_koma(
        self,
        canvas: BoardCanvas,
        row_idx: int,
        col_idx: int,
        ktype: KomaType,
        is_upside_down: bool,
    ) -> int | None:
        if ktype == KomaType.NONE:
            return None
        img = canvas.koma_image_cache.get_koma_image(
            ktype, is_upside_down=is_upside_down
        )
        x, y = self._drawing_coords.idxs_to_xy(col_idx, row_idx, centering="xy")
        return canvas.create_image(
            x, y, image=img, anchor="center", tags=("promotion_prompt",)
        )

    def clear_promotion_prompts(self, canvas: BoardCanvas) -> None:
        canvas.delete("promotion_prompt")

    def clear_highlights(self, canvas: BoardCanvas) -> None:
        self.tile_highlights.update_all_tiles(canvas, "")

    def unhighlight_square(self, canvas: BoardCanvas, sq: Square) -> None:
        if sq == Square.NONE or sq == Square.HAND:
            return
        col_idx, row_idx = self.sq_to_idxs(sq)
        img = self.board_image_cache.get_transparent_tile()
        if img is not None:
            self.tile_highlights.update_tile(canvas, img, row_idx, col_idx)

    def highlight_square(self, canvas: BoardCanvas, sq: Square) -> None:
        if sq == Square.NONE or sq == Square.HAND:
            return
        col_idx, row_idx = self.sq_to_idxs(sq)
        img = self.board_image_cache.get_selected_tile_highlight()
        if img is not None:
            self.tile_highlights.update_tile(canvas, img, row_idx, col_idx)

    def highlight_last_move_square(self, canvas: BoardCanvas, sq: Square) -> None:
        if sq == Square.NONE or sq == Square.HAND:
            return
        col_idx, row_idx = self.sq_to_idxs(sq)
        img = self.board_image_cache.get_last_move_tile_highlight()
        if img is not None:
            self.tile_highlights.update_tile(canvas, img, row_idx, col_idx)

    def _create_base_layer(self, canvas: BoardCanvas) -> int:
        x1, y1 = self._drawing_coords.idxs_to_xy(0, 0)
        x2, y2 = self._drawing_coords.idxs_to_xy(NUM_COLS, NUM_ROWS)
        id_: int = canvas.create_rectangle(x1, y1, x2, y2, fill="#ffffff")
        return id_

    def _create_tile_background_layer(self, canvas: BoardCanvas) -> None:
        self.tile_backgrounds.draw_layer(
            canvas, self._drawing_coords.idxs_to_xy, tag="board_tile"
        )

    def _create_highlight_layer(self, canvas: BoardCanvas) -> None:
        self.tile_highlights.draw_layer(
            canvas, self._drawing_coords.idxs_to_xy, tag="highlight_tile"
        )
        transparent_img = self.board_image_cache.get_transparent_tile()
        if transparent_img is not None:
            self.tile_highlights.update_all_tiles(canvas, transparent_img)

    def _create_koma_text_layer(self, canvas: BoardCanvas) -> None:
        for row_idx in range(NUM_ROWS):
            for col_idx in range(NUM_COLS):
                x, y = self._drawing_coords.idxs_to_xy(col_idx, row_idx, "xy")
                id_ = draw_board_tile_text(canvas, x, y, is_centered=True)
                self.tile_texts.set_id(row_idx, col_idx, id_)

    def _create_koma_layer(self, canvas: BoardCanvas) -> None:
        self.tile_images.draw_layer(canvas, self._drawing_coords.idxs_to_xy)

    def _create_grid_lines(self, canvas: BoardCanvas) -> None:
        for i in range(NUM_COLS + 1):
            x1, y1 = self._drawing_coords.idxs_to_xy(i, 0)
            x2, y2 = self._drawing_coords.idxs_to_xy(i, NUM_ROWS)
            canvas.create_line(x1, y1, x2, y2, fill="black", width=1)
        for j in range(NUM_ROWS + 1):
            x1, y1 = self._drawing_coords.idxs_to_xy(0, j)
            x2, y2 = self._drawing_coords.idxs_to_xy(NUM_COLS, j)
            canvas.create_line(x1, y1, x2, y2, fill="black", width=1)

    def _create_notation_labels(self, canvas: BoardCanvas) -> None:
        coords_text_size = canvas.measurements.coords_text_size
        for row_idx in range(NUM_ROWS):
            row_num = self._row_idx_to_num(row_idx)
            row_label = " " + KanjiNumber(row_num).name
            x, y = self._drawing_coords.idxs_to_xy(NUM_COLS, row_idx, centering="y")
            canvas.create_text(
                x, y, text=" " + row_label, font=("", coords_text_size), anchor="w"
            )
        for col_idx in range(NUM_COLS):
            col_num = self._col_idx_to_num(col_idx)
            x, y = self._drawing_coords.idxs_to_xy(col_idx, 0, centering="x")
            canvas.create_text(
                x, y, text=str(col_num), font=("", coords_text_size), anchor="s"
            )

    def _create_clickbox_layer(self, canvas: BoardCanvas) -> None:
        self.tile_clickboxes.draw_layer(
            canvas, self._drawing_coords.idxs_to_xy, tag="click_tile"
        )
        transparent_img = self.board_image_cache.get_transparent_tile()
        if transparent_img is not None:
            self.tile_clickboxes.update_all_tiles(canvas, transparent_img)

    def _update_base_layer(self, canvas: BoardCanvas, skin: BoardSkin) -> None:
        if self.background_id is not None:
            canvas.itemconfig(self.background_id, fill=skin.colour)

    def _update_tile_backgrounds(
        self, canvas: BoardCanvas, img: ImageTk.PhotoImage
    ) -> None:
        self.tile_backgrounds.update_all_tiles(canvas, img)

    def clickboxes(self) -> Iterator[tuple[Square, int]]:
        for (row_idx, col_idx), id_ in self.tile_clickboxes:
            sq = Square.from_cr(
                self._col_idx_to_num(col_idx), self._row_idx_to_num(row_idx)
            )
            if id_ is not None:
                yield (sq, id_)

    def _col_idx_to_num(self, col_idx: int) -> int:
        return col_idx + 1 if self.is_upside_down else NUM_COLS - col_idx

    def _row_idx_to_num(self, row_idx: int) -> int:
        return NUM_ROWS - row_idx if self.is_upside_down else row_idx + 1

    def _col_num_to_idx(self, col_num: int) -> int:
        return col_num - 1 if self.is_upside_down else NUM_COLS - col_num

    def _row_num_to_idx(self, row_num: int) -> int:
        return NUM_ROWS - row_num if self.is_upside_down else row_num - 1

    def sq_to_idxs(self, sq: Square) -> tuple[int, int]:
        col_num, row_num = sq.get_cr()
        col_idx = self._col_num_to_idx(col_num)
        row_idx = self._row_num_to_idx(row_num)
        return col_idx, row_idx


class BoardDrawingCoords:
    def __init__(
        self, sq_width: float, sq_height: float, board_top_left_xy: tuple[float, float]
    ) -> None:
        self.update_coords(sq_width, sq_height, board_top_left_xy)

    def update_coords(
        self, sq_width: float, sq_height: float, board_top_left_xy: tuple[float, float]
    ) -> None:
        self._sq_w = sq_width
        self._sq_h = sq_height
        self._board_top_left_x, self._board_top_left_y = board_top_left_xy

    def idxs_to_xy(
        self, col_idx: int, row_idx: int, centering: str = ""
    ) -> tuple[int, int]:
        x_offset = 0.5 * self._sq_w if "x" in centering.lower() else 0
        y_offset = 0.5 * self._sq_h if "y" in centering.lower() else 0
        x = self._board_top_left_x + col_idx * self._sq_w + x_offset
        y = self._board_top_left_y + row_idx * self._sq_h + y_offset
        return int(x), int(y)


class TileIdStore:
    def __init__(
        self, num_cols: int, num_rows: int, default: int | None = None
    ) -> None:
        self.tiles = [[default] * num_cols for _ in range(num_rows)]

    def __iter__(self) -> Iterator[tuple[tuple[int, int], int | None]]:
        for row_idx, row in enumerate(self.tiles):
            for col_idx, id_ in enumerate(row):
                yield ((row_idx, col_idx), id_)

    def set_id(self, row_idx: int, col_idx: int, id_: int) -> None:
        self.tiles[row_idx][col_idx] = id_

    def get_id(self, row_idx: int, col_idx: int) -> int | None:
        return self.tiles[row_idx][col_idx]


class BoardImageLayer:
    def __init__(self, is_centered: bool = False) -> None:
        self.is_centered = is_centered
        # Stored canvas item ids for later alteration.
        # FEN ordering. (row_idx, col_idx), zero-based
        self.tiles: list[list[int | None]] = [[-1] * NUM_COLS for _ in range(NUM_ROWS)]

    def __iter__(self) -> Iterator[tuple[tuple[int, int], int | None]]:
        for row_idx, row in enumerate(self.tiles):
            for col_idx, id_ in enumerate(row):
                yield ((row_idx, col_idx), id_)

    def draw_layer(
        self,
        canvas: BoardCanvas,
        idxs_to_xy: Callable[[int, int, str], tuple[int, int]],
        tag: str = "",
    ) -> None:
        for row_idx, row in enumerate(self.tiles):
            for col_idx, _ in enumerate(row):
                x, y = idxs_to_xy(col_idx, row_idx, "xy" if self.is_centered else "")
                id_ = draw_board_tile_image(canvas, x, y, self.is_centered, tag)
                self.tiles[row_idx][col_idx] = id_

    def get_id(self, row_idx: int, col_idx: int) -> int | None:
        return self.tiles[row_idx][col_idx]

    def update_tile(
        self, canvas: BoardCanvas, img: ImageTk.PhotoImage, row_idx: int, col_idx: int
    ) -> None:
        id_ = self.get_id(row_idx, col_idx)
        if id_ is not None:
            canvas.itemconfig(id_, image=img)

    def update_all_tiles(
        self, canvas: BoardCanvas, img: ImageTk.PhotoImage | Literal[""]
    ) -> None:
        for row in self.tiles:
            for id_ in row:
                if id_ is not None:
                    canvas.itemconfig(id_, image=img)


def draw_board_tile_image(
    canvas: BoardCanvas, x: int, y: int, is_centered: bool, tag: str = ""
) -> int:
    return canvas.create_image(
        x, y, image="", anchor="center" if is_centered else "nw", tags=tag
    )


def draw_board_tile_text(
    canvas: BoardCanvas, x: int, y: int, is_centered: bool, tag: str = ""
) -> int:
    return canvas.create_text(
        x,
        y,
        text="",
        font=("", canvas.measurements.sq_text_size),
        anchor="center" if is_centered else "nw",
        tags=tag,
    )
