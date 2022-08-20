from __future__ import annotations


class BoardMeasurements:
    """Parameter object calculating and storing the various
    measurements of the shogiban.
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

    def __init__(self, width: int, height: int) -> None:
        # could refactor into a dictionary perhaps?
        (
            self.sq_w, self.sq_h, self.komadai_w, self.w_pad, self.h_pad,
            self.komadai_piece_size, self.sq_text_size, self.komadai_text_size,
            self.coords_text_size, self.x_sq, self.y_sq
        ) = self.recalculate_sizes(width, height)
        return

    def recalculate_sizes(self, canvas_width: int, canvas_height: int):
        """Geometry: 9x9 shogi board, flanked by komadai area on
        either side. Padded on all 4 sides (canvas internal padding).
        Extra space allocated between board and right komadai (2 times
        coord text size) to accomodate board coordinates drawn there.
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
        w_pad: float
        h_pad: float
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
