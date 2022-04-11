from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KanjiNumber

if TYPE_CHECKING:
    from PIL import ImageTk
    from tsumemi.src.tsumemi.board_canvas import BoardCanvas


# Shogi board dimensions in squares
NUM_COLS = 9
NUM_ROWS = 9


class BoardLayer(ABC):
    def __init__(self) -> None:
        self.tiles = [[-1] * NUM_COLS for i in range(NUM_ROWS)]
        return

    @abstractmethod
    def draw_layer(self, canvas: BoardCanvas, tag: str = "") -> None:
        raise NotImplementedError


class BoardImageLayer(BoardLayer):
    def draw_layer(self, canvas: BoardCanvas, tag: str = "") -> None:
        for row_idx in range(NUM_ROWS):
            for col_idx in range(NUM_COLS):
                id_ = canvas.create_image(
                    *canvas.idxs_to_xy(col_idx, row_idx),
                    image="",
                    anchor="nw",
                    tags=tag,
                )
                self.tiles[row_idx][col_idx] = id_
        return

    def update_tile(self,
            canvas: BoardCanvas,
            img: ImageTk.PhotoImage,
            row_idx: int,
            col_idx: int
        ) -> None:
        canvas.itemconfig(self.tiles[row_idx][col_idx], image=img)
        return

    def update_all_tiles(self, canvas: BoardCanvas, img: ImageTk.PhotoImage
        ) -> None:
        for row in self.tiles:
            for tile in row:
                canvas.itemconfig(tile, image=img)
        return


class BoardKomaTextLayer(BoardLayer):
    def draw_layer(self, canvas: BoardCanvas, tag: str = "") -> None:
        for row_idx in range(NUM_ROWS):
            for col_idx in range(NUM_COLS):
                id_ = canvas.create_text(
                    *canvas.idxs_to_xy(col_idx, row_idx, centering="xy"),
                    text="",
                    font=("", canvas.measurements.sq_text_size),
                    anchor="center",
                    tags=tag,
                )
                self.tiles[row_idx][col_idx] = id_
        return


class BoardArtist:
    def __init__(self) -> None:
        # Stored canvas item ids for later alteration.
        # FEN ordering. (row_idx, col_idx), zero-based
        self.board_rect = -1
        self.board_tile_layer = BoardImageLayer()
        self.highlight_layer = BoardImageLayer()
        return

    def update_board_tile_images(self,
            canvas: BoardCanvas, img: ImageTk.PhotoImage
        ) -> None:
        self.board_tile_layer.update_all_tiles(canvas, img)
        return

    def draw_board_base_layer(self, canvas: BoardCanvas) -> int:
        id_: int = canvas.create_rectangle(
            *canvas.idxs_to_xy(0, 0),
            *canvas.idxs_to_xy(NUM_COLS, NUM_ROWS),
            fill="#ffffff",
        )
        self.board_rect = id_
        return id_

    def draw_board_tile_layer(self, canvas: BoardCanvas) -> None:
        self.board_tile_layer.draw_layer(canvas, tag="board_tile")
        return

    def draw_board_focus_layer(self, canvas: BoardCanvas) -> None:
        self.highlight_layer.draw_layer(canvas, tag="highlight_tile")
        transparent_img = canvas.board_img_cache.get_dict()["transparent"]
        self.highlight_layer.update_all_tiles(canvas, transparent_img)
        return

    def draw_board_coordinates(self, canvas: BoardCanvas) -> None:
        coords_text_size = canvas.measurements.coords_text_size
        for row_idx in range(NUM_ROWS):
            row_num = canvas.row_idx_to_num(row_idx)
            row_label = " " + KanjiNumber(row_num).name
            canvas.create_text(
                *canvas.idxs_to_xy(NUM_COLS, row_idx, centering="y"),
                text=" " + row_label,
                font=("", coords_text_size),
                anchor="w",
            )
        for col_idx in range(9):
            col_num = canvas.col_idx_to_num(col_idx)
            canvas.create_text(
                *canvas.idxs_to_xy(col_idx, 0, centering="x"),
                text=str(col_num),
                font=("", coords_text_size),
                anchor="s",
            )
        return

    def draw_board_grid_lines(self, canvas: BoardCanvas) -> None:
        for i in range(NUM_COLS+1):
            canvas.create_line(
                *canvas.idxs_to_xy(i, 0),
                *canvas.idxs_to_xy(i, NUM_ROWS),
                fill="black", width=1,
            )
        for j in range(NUM_ROWS+1):
            canvas.create_line(
                *canvas.idxs_to_xy(0, j),
                *canvas.idxs_to_xy(NUM_COLS, j),
                fill="black", width=1,
            )
        return

    def unhighlight_square(self,
            canvas: BoardCanvas, row_idx: int, col_idx: int
        ) -> None:
        img = canvas.board_img_cache.get_dict()["transparent"]
        self.highlight_layer.update_tile(canvas, img, row_idx, col_idx)
        return

    def highlight_square(self,
            canvas: BoardCanvas, row_idx: int, col_idx: int
        ) -> None:
        img = canvas.board_img_cache.get_dict()["highlight"]
        self.highlight_layer.update_tile(canvas, img, row_idx, col_idx)
        return
