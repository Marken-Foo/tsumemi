from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable


class BoardMeasurements:
    """Parameter object calculating and storing the various
    measurements of the shogiban.
    """
    INNER_H_PAD: int = 30 # pixels
    INNER_W_PAD: int = 10 # pixels
    # Constant proportions; base unit is square width.
    COORD_TEXT_IN_SQ: float = 2/9
    KOMADAI_PIECE_RATIO: float = 4/5 # komadai piece : board piece size ratio
    KOMADAI_TEXT_IN_SQ: float = 2/5
    KOMADAI_W_IN_SQ: float = 2
    SQ_ASPECT_RATIO: float = 11/12
    SQ_TEXT_IN_SQ: float = 7/10

    def __init__(self, width: int, height: int) -> None:
        self.sq_w: float
        self.sq_h: float
        self.komadai_w: float
        self.w_pad: float
        self.h_pad: float
        self.komadai_piece_size: int
        self.sq_text_size: int
        self.komadai_text_size: int
        self.coords_text_size: int
        self.x_sq: Callable[[float], float]
        self.y_sq: Callable[[float], float]
        self.recalculate_sizes(width, height)
        return

    def recalculate_sizes(self, canvas_width: int, canvas_height: int) -> None:
        """Geometry: 9x9 shogi board, flanked by komadai area on
        either side. Padded on all 4 sides (canvas internal padding).
        Extra space allocated between board and right komadai (2 times
        coord text size) to accomodate board coordinates drawn there.
        """
        max_sq_w = self._calc_max_sq_w(canvas_width)
        sq_w = self.set_sq_w(canvas_width, canvas_height)

        # Propagate other measurements
        sq_h = sq_w / self.SQ_ASPECT_RATIO
        self.sq_h = sq_h

        # Set text and komadai attributes
        coords_text_size = self.set_text_sizes(sq_w)
        komadai_w = self.set_komadai_sizes(sq_w)
        w_pad: float
        h_pad: float
        if int(sq_w) == int(max_sq_w):
            w_pad = self.INNER_W_PAD
            h_pad = (canvas_height - 9*sq_h) / 2
        else:
            w_pad = (canvas_width - 2*komadai_w
                     - 2*coords_text_size - 9*sq_w) / 2
            h_pad = self.INNER_H_PAD
        self.w_pad = w_pad
        self.h_pad = h_pad
        # Useful helper functions. Argument is row/col number of square.
        def x_sq(i: float) -> float:
            return w_pad + komadai_w + sq_w * i
        def y_sq(j: float) -> float:
            return h_pad + sq_h * j

        self.x_sq = x_sq
        self.y_sq = y_sq
        return

    def _calc_max_sq_w(self, canvas_w: int) -> float:
        return ((canvas_w - 2*self.INNER_W_PAD)
            / (9 + 2*self.KOMADAI_W_IN_SQ + 2*self.COORD_TEXT_IN_SQ))

    def _calc_max_sq_h(self, canvas_h: int) -> float:
        return (canvas_h - 2*self.INNER_H_PAD) / 9

    def set_sq_w(self, canvas_w: int, canvas_h: int) -> float:
        max_sq_w = self._calc_max_sq_w(canvas_w)
        max_sq_h = self._calc_max_sq_h(canvas_h)
        sq_w = min(max_sq_w, max_sq_h*self.SQ_ASPECT_RATIO)
        self.sq_w = sq_w
        return sq_w

    def set_text_sizes(self, sq_w: float) -> int:
        coords_text_size = int(sq_w * self.COORD_TEXT_IN_SQ)
        self.sq_text_size = int(sq_w * self.SQ_TEXT_IN_SQ)
        self.coords_text_size = coords_text_size
        return coords_text_size

    def set_komadai_sizes(self, sq_w: float) -> float:
        self.komadai_piece_size = int(sq_w * self.KOMADAI_PIECE_RATIO)
        self.komadai_text_size = int(sq_w * self.KOMADAI_TEXT_IN_SQ)
        komadai_w = sq_w * self.KOMADAI_W_IN_SQ
        self.komadai_w = komadai_w
        return komadai_w
