from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KanjiNumber

if TYPE_CHECKING:
    from tsumemi.src.tsumemi.board_canvas import BoardCanvas


# Shogi board dimensions in squares
NUM_COLS = 9
NUM_ROWS = 9


class BoardArtist:
    def __init__(self) -> None:
        # Stored canvas item ids for later alteration.
        # FEN ordering. (row_idx, col_idx), zero-based
        self.board_rect = -1
        self.board_tiles = [[-1] * NUM_COLS for i in range(NUM_ROWS)]
        self.board_select_tiles = [[-1] * NUM_COLS for i in range(NUM_ROWS)]
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
        for row_idx in range(NUM_ROWS):
            for col_idx in range(NUM_COLS):
                id_ = canvas.create_image(
                    *canvas.idxs_to_xy(col_idx, row_idx),
                    image="",
                    anchor="nw",
                )
                self.board_tiles[row_idx][col_idx] = id_
        return

    def draw_board_focus_layer(self, canvas: BoardCanvas) -> None:
        for row_idx in range(NUM_ROWS):
            for col_idx in range(NUM_COLS):
                id_ = canvas.create_image(
                    *canvas.idxs_to_xy(col_idx, row_idx),
                    image=canvas.board_img_cache.get_dict()["transparent"],
                    anchor="nw",
                )
                self.board_select_tiles[row_idx][col_idx] = id_
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
        img_idx = self.board_select_tiles[row_idx][col_idx]
        canvas.itemconfig(
            img_idx, image=canvas.board_img_cache.get_dict()["transparent"]
        )
        return

    def highlight_square(self,
            canvas: BoardCanvas, row_idx: int, col_idx: int
        ) -> None:
        img_idx = self.board_select_tiles[row_idx][col_idx]
        canvas.itemconfig(
            img_idx, image=canvas.board_img_cache.get_dict()["highlight"]
        )
        return
