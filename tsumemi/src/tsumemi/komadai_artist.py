from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import HAND_TYPES

if TYPE_CHECKING:
    from tsumemi.src.shogi.basetypes import KomaType
    from tsumemi.src.shogi.position_internals import HandRepresentation
    from tsumemi.src.tsumemi.board_canvas import BoardCanvas


class KomadaiArtist:
    def __init__(self,
            x_anchor: int,
            y_anchor: int,
            canvas: BoardCanvas,
            hand: HandRepresentation,
            is_sente: bool,
            align="top",
        ) -> None:
        self.is_sente = is_sente
        is_text = canvas.is_text()
        self.text_size = canvas.measurements.komadai_text_size
        # Actual size of each character in px is about 1.5*text_size
        char_height = 1.5 * self.text_size
        self.piece_size = canvas.measurements.komadai_piece_size
        self.symbol_size = (
            self.text_size * 3/2 if is_text
            else self.piece_size
        )
        self.pad = (
            self.text_size / 8 if is_text
            else self.piece_size / 8
        )
        self.mochigoma_heading_size = 4 * char_height # "▲\n持\n駒\n"
        
        self.hand_counts = {}
        for ktype in HAND_TYPES:
            count = hand.get_komatype_count(ktype)
            if count > 0:
                self.hand_counts[ktype] = count
        
        self.width: int = 2 * self.piece_size
        self.height: int = self.mochigoma_heading_size + (
            2 * char_height if not self.hand_counts
            else len(self.hand_counts)*(self.symbol_size + self.pad) - self.pad
        )
        self.x_anchor: int = x_anchor
        self.y_anchor: int = y_anchor - self.height if align == "bottom" else y_anchor
        return
    
    def draw_all_komadai_koma(self, canvas: BoardCanvas) -> None:
        if not self.hand_counts:
            self.draw_komadai_text_nashi(canvas)
            return
        for n, (ktype, count) in enumerate(self.hand_counts.items()):
            y_offset = (
                self.mochigoma_heading_size
                + n*(self.symbol_size+self.pad)
                + self.symbol_size/2 # for the anchor="center"
            )
            self.draw_komadai_koma_group(canvas, y_offset, ktype, count)
        return
    
    def draw_komadai_base(self, canvas: BoardCanvas) -> int:
        id: int = canvas.create_rectangle(
            self.x_anchor-(self.width/2), self.y_anchor,
            self.x_anchor+(self.width/2), self.y_anchor+self.height,
            fill="#ffffff",
            outline="",
            tags=("komadai-solid",)
        )
        return id
    
    def draw_komadai_header_text(self, canvas: BoardCanvas) -> int:
        header_text = "▲\n持\n駒" if self.is_sente else "△\n持\n駒"
        id: int = canvas.create_text(
            self.x_anchor, self.y_anchor,
            text=header_text,
            font=("", self.text_size),
            anchor="n"
        )
        return id
    
    def draw_komadai_text_nashi(self, canvas: BoardCanvas) -> int:
        id: int = canvas.create_text(
            self.x_anchor, self.y_anchor+self.mochigoma_heading_size,
            text="な\nし",
            font=("", self.text_size),
            anchor="n"
        )
        return id
    
    def draw_komadai_koma_group(self,
            canvas: BoardCanvas,
            y_offset: float,
            ktype: KomaType,
            count: int,
        ) -> int:
        # returns the id of the koma drawing
        self._draw_komadai_focus_tile(canvas, y_offset, ktype)
        id: int = self._draw_komadai_koma(canvas, y_offset, ktype)
        self._draw_komadai_koma_count(canvas, y_offset, count)
        return id
    
    def _draw_komadai_focus_tile(self,
            canvas: BoardCanvas,
            y_offset: float,
            ktype: KomaType,
        ) -> int:
        id: int = canvas.create_image(
            self.x_anchor-(self.width/5),
            self.y_anchor+y_offset,
            image="",
            anchor="center",
            tags=(
                "komadai_focus",
                ktype.to_csa(),
                "sente" if self.is_sente else "gote"
            ),
        )
        return id
    
    def _draw_komadai_koma(self,
            canvas: BoardCanvas,
            y_offset: float,
            ktype: KomaType,
        ) -> int:
        artist = canvas.make_koma_artist(invert=False, komadai=True)
        id: int = artist.draw_koma(
            canvas,
            self.x_anchor-(self.width/5),
            self.y_anchor+y_offset,
            ktype=ktype,
            anchor="center",
            tags=(
                "komadai_koma",
                ktype.to_csa(),
                "sente" if self.is_sente else "gote"
            ),
        )
        return id
    
    def _draw_komadai_koma_count(self,
            canvas: BoardCanvas,
            y_offset: float,
            count: int,
        ) -> int:
        id: int = canvas.create_text(
            self.x_anchor+0.5*self.piece_size,
            self.y_anchor+y_offset,
            text=str(count),
            font=("", self.text_size),
            anchor="center"
        )
        return id
