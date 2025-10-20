from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KomaType
from tsumemi.src.shogi.square import KanjiNumber
from tsumemi.src.tsumemi.board_gui.board_image_cache import BoardImageCache
from tsumemi.src.tsumemi.board_gui.board_meas import BoardMeasurements

if TYPE_CHECKING:
    from collections.abc import Callable
    from PIL import ImageTk
    from tsumemi.src.tsumemi.board_gui.board_canvas import BoardCanvas
    from tsumemi.src.tsumemi.skins import BoardSkin


# Shogi board dimensions in squares
NUM_COLS = 9
NUM_ROWS = 9


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


class BoardLayer(ABC):
    def __init__(self, is_centered: bool = False) -> None:
        self.is_centered = is_centered
        # Stored canvas item ids for later alteration.
        # FEN ordering. (row_idx, col_idx), zero-based
        self.tiles = [[-1] * NUM_COLS for _ in range(NUM_ROWS)]

    @abstractmethod
    def draw_layer(
        self,
        canvas: BoardCanvas,
        idxs_to_xy: Callable[[int, int, str], tuple[int, int]],
        tag: str = "",
    ) -> None:
        raise NotImplementedError


class BoardImageLayer(BoardLayer):
    def draw_layer(
        self,
        canvas: BoardCanvas,
        idxs_to_xy: Callable[[int, int, str], tuple[int, int]],
        tag: str = "",
    ) -> None:
        for row_idx in range(NUM_ROWS):
            for col_idx in range(NUM_COLS):
                x, y = idxs_to_xy(col_idx, row_idx, "xy" if self.is_centered else "")
                id_ = draw_board_tile_image(canvas, x, y, self.is_centered, tag)
                self.tiles[row_idx][col_idx] = id_

    def update_tile(
        self, canvas: BoardCanvas, img: ImageTk.PhotoImage, row_idx: int, col_idx: int
    ) -> None:
        canvas.itemconfig(self.tiles[row_idx][col_idx], image=img)

    def update_all_tiles(self, canvas: BoardCanvas, img: ImageTk.PhotoImage) -> None:
        for row in self.tiles:
            for tile in row:
                canvas.itemconfig(tile, image=img)


class BoardKomaTextLayer(BoardLayer):
    def draw_layer(
        self,
        canvas: BoardCanvas,
        idxs_to_xy: Callable[[int, int, str], tuple[int, int]],
        tag: str = "",
    ) -> None:
        for row_idx in range(NUM_ROWS):
            for col_idx in range(NUM_COLS):
                x, y = idxs_to_xy(col_idx, row_idx, "xy" if self.is_centered else "")
                id_ = draw_board_tile_text(canvas, x, y, self.is_centered, tag)
                self.tiles[row_idx][col_idx] = id_


class BoardArtist:
    def __init__(self, measurements: BoardMeasurements, skin: BoardSkin) -> None:
        self.board_rect = -1
        self.board_tile_layer = BoardImageLayer()
        self.highlight_layer = BoardImageLayer()
        self.koma_image_layer = BoardImageLayer(is_centered=True)
        self.koma_text_layer = BoardKomaTextLayer(is_centered=True)
        self.click_layer = BoardImageLayer()
        self.board_image_cache = BoardImageCache(
            measurements.sq_w, measurements.sq_h, skin
        )
        self._drawing_coords = BoardDrawingCoords(
            measurements.sq_w, measurements.sq_h, measurements.get_board_top_left_xy()
        )

    def draw_board(self, canvas: BoardCanvas) -> None:
        self._draw_board_base_layer(canvas)
        self._draw_board_tile_layer(canvas)
        self._draw_board_focus_layer(canvas)
        self._draw_koma_text_layer(canvas)
        self._draw_koma_image_layer(canvas)
        self._draw_board_grid_lines(canvas)
        self._draw_board_coordinates(canvas)
        self._draw_click_layer(canvas)
        self._update_board_base_colour(canvas)
        if not self.board_image_cache.skin.path:
            return

        board_image = self.board_image_cache.get_board_image()
        if board_image is not None:
            self._update_board_tile_images(canvas, board_image)

    def apply_skin(self, canvas: BoardCanvas, skin: BoardSkin) -> None:
        canvas.itemconfig(self.board_rect, fill=skin.colour)
        self.board_image_cache.update_skin(skin)

    def update_measurements(
        self, sq_width: float, sq_height: float, board_top_left_xy: tuple[float, float]
    ) -> None:
        self.board_image_cache.update_dimensions(sq_width, sq_height)
        self._drawing_coords.update_coords(
            sq_width=sq_width,
            sq_height=sq_height,
            board_top_left_xy=board_top_left_xy,
        )

    def draw_koma(
        self,
        canvas: BoardCanvas,
        img: ImageTk.PhotoImage,
        row_idx: int,
        col_idx: int,
    ) -> None:
        self.koma_image_layer.update_tile(canvas, img, row_idx, col_idx)

    def draw_text_koma(
        self,
        canvas: BoardCanvas,
        text: str,
        invert: bool,
        row_idx: int,
        col_idx: int,
    ) -> None:
        canvas.itemconfig(
            self.koma_text_layer.tiles[row_idx][col_idx],
            text=text,
            angle=180 if invert else 0,
        )

    def lift_click_layer(self, canvas: BoardCanvas) -> None:
        canvas.lift("click_tile")

    def draw_promotion_cover(self, canvas: BoardCanvas) -> int | None:
        img = self.board_image_cache.get_semi_transparent_board_cover()
        if img is None:
            return None
        x, y = self._drawing_coords.idxs_to_xy(0, 0)
        return canvas.create_image(
            x, y, image=img, anchor="nw", tags="promotion_prompt"
        )

    def draw_promotion_prompt_koma(
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

    def unhighlight_square(
        self, canvas: BoardCanvas, row_idx: int, col_idx: int
    ) -> None:
        img = self.board_image_cache.get_transparent_tile()
        if img is not None:
            self.highlight_layer.update_tile(canvas, img, row_idx, col_idx)

    def highlight_square(self, canvas: BoardCanvas, row_idx: int, col_idx: int) -> None:
        img = self.board_image_cache.get_selected_tile_highlight()
        if img is not None:
            self.highlight_layer.update_tile(canvas, img, row_idx, col_idx)

    def highlight_square_2(
        self, canvas: BoardCanvas, row_idx: int, col_idx: int
    ) -> None:
        img = self.board_image_cache.get_last_move_tile_highlight()
        if img is not None:
            self.highlight_layer.update_tile(canvas, img, row_idx, col_idx)

    def _draw_board_base_layer(self, canvas: BoardCanvas) -> int:
        x1, y1 = self._drawing_coords.idxs_to_xy(0, 0)
        x2, y2 = self._drawing_coords.idxs_to_xy(NUM_COLS, NUM_ROWS)
        id_: int = canvas.create_rectangle(x1, y1, x2, y2, fill="#ffffff")
        self.board_rect = id_
        return id_

    def _draw_board_tile_layer(self, canvas: BoardCanvas) -> None:
        self.board_tile_layer.draw_layer(
            canvas, self._drawing_coords.idxs_to_xy, tag="board_tile"
        )

    def _draw_board_focus_layer(self, canvas: BoardCanvas) -> None:
        self.highlight_layer.draw_layer(
            canvas, self._drawing_coords.idxs_to_xy, tag="highlight_tile"
        )
        transparent_img = self.board_image_cache.get_transparent_tile()
        if transparent_img is not None:
            self.highlight_layer.update_all_tiles(canvas, transparent_img)

    def _draw_koma_text_layer(self, canvas: BoardCanvas) -> None:
        self.koma_text_layer.draw_layer(canvas, self._drawing_coords.idxs_to_xy)

    def _draw_koma_image_layer(self, canvas: BoardCanvas) -> None:
        self.koma_image_layer.draw_layer(canvas, self._drawing_coords.idxs_to_xy)

    def _draw_board_grid_lines(self, canvas: BoardCanvas) -> None:
        for i in range(NUM_COLS + 1):
            x1, y1 = self._drawing_coords.idxs_to_xy(i, 0)
            x2, y2 = self._drawing_coords.idxs_to_xy(i, NUM_ROWS)
            canvas.create_line(x1, y1, x2, y2, fill="black", width=1)
        for j in range(NUM_ROWS + 1):
            x1, y1 = self._drawing_coords.idxs_to_xy(0, j)
            x2, y2 = self._drawing_coords.idxs_to_xy(NUM_COLS, j)
            canvas.create_line(x1, y1, x2, y2, fill="black", width=1)

    def _draw_board_coordinates(self, canvas: BoardCanvas) -> None:
        coords_text_size = canvas.measurements.coords_text_size
        for row_idx in range(NUM_ROWS):
            row_num = canvas.row_idx_to_num(row_idx)
            row_label = " " + KanjiNumber(row_num).name
            x, y = self._drawing_coords.idxs_to_xy(NUM_COLS, row_idx, centering="y")
            canvas.create_text(
                x, y, text=" " + row_label, font=("", coords_text_size), anchor="w"
            )
        for col_idx in range(9):
            col_num = canvas.col_idx_to_num(col_idx)
            x, y = self._drawing_coords.idxs_to_xy(col_idx, 0, centering="x")
            canvas.create_text(
                x, y, text=str(col_num), font=("", coords_text_size), anchor="s"
            )

    def _draw_click_layer(self, canvas: BoardCanvas) -> None:
        self.click_layer.draw_layer(
            canvas, self._drawing_coords.idxs_to_xy, tag="click_tile"
        )
        transparent_img = self.board_image_cache.get_transparent_tile()
        if transparent_img is not None:
            self.click_layer.update_all_tiles(canvas, transparent_img)

    def _update_board_base_colour(self, canvas: BoardCanvas) -> None:
        base_colour = self.board_image_cache.skin.colour
        canvas.itemconfig(self.board_rect, fill=base_colour)

    def _update_board_tile_images(
        self, canvas: BoardCanvas, img: ImageTk.PhotoImage
    ) -> None:
        self.board_tile_layer.update_all_tiles(canvas, img)
