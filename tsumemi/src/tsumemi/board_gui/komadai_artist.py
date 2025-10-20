from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import HAND_TYPES, KANJI_FROM_KTYPE
from tsumemi.src.tsumemi.skins import BoardSkin

if TYPE_CHECKING:
    from tsumemi.src.shogi.basetypes import KomaType
    from tsumemi.src.shogi.position_internals import HandRepresentation
    from tsumemi.src.tsumemi.board_gui.board_canvas import BoardCanvas
    from tsumemi.src.tsumemi.board_gui.board_meas import BoardMeasurements


def komadai_width(koma_size: int) -> int:
    return 2 * koma_size


def komadai_height(
    heading_height: float,
    char_height: float,
    num_koma_types: int,
    koma_height: float,
    koma_vertical_padding: float,
) -> int:
    if num_koma_types <= 0:
        return int(heading_height + 2 * char_height)
    else:
        return int(
            heading_height
            + num_koma_types * (koma_height + koma_vertical_padding)
            - koma_vertical_padding
        )


def _koma_group_offset(
    n: int, heading_height: float, koma_height: float, koma_vertical_padding: float
) -> float:
    return (
        heading_height
        + n * (koma_height + koma_vertical_padding)
        + koma_height / 2  # for the anchor="center"
    )


class KomadaiArtist:
    def __init__(
        self,
        measurements: BoardMeasurements,
        is_north: bool,  # North side or south
        is_text: bool,
        hand: HandRepresentation,
        is_sente: bool,
        align: str = "top",
    ) -> None:
        x_anchor, y_anchor = (
            measurements.get_north_komadai_anchor()
            if is_north
            else measurements.get_south_komadai_anchor()
        )

        self.is_sente = is_sente
        self.text_size = measurements.komadai_text_size
        # Actual size of each character in px is about 1.5*text_size
        char_height = 1.5 * self.text_size
        piece_size = measurements.komadai_piece_size
        self.koma_size = self.text_size * 3 / 2 if is_text else piece_size
        self.vertical_pad = self.text_size / 8 if is_text else piece_size / 8
        self.mochigoma_heading_size = 4 * char_height  # "▲\n持\n駒\n"

        self.hand_counts: dict[KomaType, int] = {}
        for ktype in HAND_TYPES:
            count = hand.get_komatype_count(ktype)
            if count > 0:
                self.hand_counts[ktype] = count

        self.width: int = komadai_width(piece_size)
        self.height: int = komadai_height(
            self.mochigoma_heading_size,
            char_height,
            len(self.hand_counts),
            self.koma_size,
            self.vertical_pad,
        )
        self.x_origin: int = int(x_anchor - self.width / 2)
        self.y_origin: int = int(
            y_anchor - self.height if align == "bottom" else y_anchor
        )

    def draw_komadai(self, canvas: BoardCanvas) -> None:
        komadai_base = self._draw_komadai_base(canvas)
        skin = canvas.komadai_skin
        assert isinstance(skin, BoardSkin)
        canvas.itemconfig(komadai_base, fill=skin.colour)
        self._draw_komadai_header_text(canvas)
        self._draw_all_komadai_koma(canvas)

    def _draw_all_komadai_koma(self, canvas: BoardCanvas) -> None:
        if not self.hand_counts:
            self._draw_komadai_text_nashi(canvas)
            return
        for n, (ktype, count) in enumerate(self.hand_counts.items()):
            y_offset = _koma_group_offset(
                n, self.mochigoma_heading_size, self.koma_size, self.vertical_pad
            )
            self._draw_komadai_koma_group(canvas, y_offset, ktype, count)

    def _draw_komadai_base(self, canvas: BoardCanvas) -> int:
        return canvas.create_rectangle(
            self.x_origin,
            self.y_origin,
            self.x_origin + self.width,
            self.y_origin + self.height,
            fill="#ffffff",
            outline="",
            tags=("komadai-solid",),
        )

    def _draw_komadai_header_text(self, canvas: BoardCanvas) -> int:
        header_text = "▲\n持\n駒" if self.is_sente else "△\n持\n駒"
        id_: int = canvas.create_text(
            self.x_origin + self.width / 2,
            self.y_origin,
            text=header_text,
            font=("", self.text_size),
            anchor="n",
        )
        return id_

    def _draw_komadai_text_nashi(self, canvas: BoardCanvas) -> int:
        id_: int = canvas.create_text(
            self.x_origin + self.width / 2,
            self.y_origin + self.mochigoma_heading_size,
            text="な\nし",
            font=("", self.text_size),
            anchor="n",
        )
        return id_

    def _draw_komadai_koma_group(
        self,
        canvas: BoardCanvas,
        y_offset: float,
        ktype: KomaType,
        count: int,
    ) -> None:
        x = self.x_origin + self.width / 2 - self.width / 5
        y = self.y_origin + y_offset
        self._draw_komadai_focus_tile(canvas, x, y, ktype)
        self._draw_komadai_koma(canvas, x, y, ktype)

        x = self.x_origin + self.width / 2 + 0.5 * self.koma_size
        self._draw_komadai_koma_count(canvas, x, y, count)

    def _draw_komadai_focus_tile(
        self,
        canvas: BoardCanvas,
        x: float,
        y: float,
        ktype: KomaType,
    ) -> int:
        tags = (
            "komadai_focus",
            ktype.to_csa(),
            "sente" if self.is_sente else "gote",
        )
        id_: int = canvas.create_image(x, y, image="", anchor="center", tags=tags)
        return id_

    def _draw_komadai_koma(
        self, canvas: BoardCanvas, x: float, y: float, ktype: KomaType
    ) -> int:
        tags = ("komadai_koma", ktype.to_csa(), "sente" if self.is_sente else "gote")
        if canvas.is_text():
            return self._draw_komadai_koma_text(canvas, x, y, ktype, tags)
        else:
            return self._draw_komadai_koma_image(canvas, x, y, ktype, tags)

    def _draw_komadai_koma_image(
        self,
        canvas: BoardCanvas,
        x: float,
        y: float,
        ktype: KomaType,
        tags: tuple[str, ...],
    ) -> int:
        img = canvas.komadai_koma_image_cache.get_koma_image(
            ktype, is_upside_down=False
        )
        return canvas.create_image(x, y, image=img, anchor="center", tags=tags)

    def _draw_komadai_koma_text(
        self,
        canvas: BoardCanvas,
        x: float,
        y: float,
        ktype: KomaType,
        tags: tuple[str, ...],
    ) -> int:
        text_size = canvas.measurements.komadai_text_size
        return canvas.create_text(  # type: ignore
            x,
            y,
            text=str(KANJI_FROM_KTYPE[ktype]),
            font=("", text_size),
            angle=0,
            anchor="center",
            tags=tags,
        )

    def _draw_komadai_koma_count(
        self,
        canvas: BoardCanvas,
        x: float,
        y: float,
        count: int,
    ) -> int:
        return canvas.create_text(
            x, y, text=str(count), font=("", self.text_size), anchor="center"
        )
