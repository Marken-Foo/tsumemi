from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import HAND_TYPES, KANJI_FROM_KTYPE, Side
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
        side: Side,
    ) -> None:
        self.measurements = measurements
        self.is_north: bool = is_north
        self.is_sente: bool = side.is_sente()
        self.is_text = is_text
        self.hand_counts: dict[KomaType, int] = {}
        self.update_measurements(measurements)

    def update_measurements(self, measurements: BoardMeasurements) -> None:
        self.measurements = measurements
        self._update_content_measurements(measurements)
        self._update_origin_and_height(len(self.hand_counts))

    def _update_content_measurements(self, measurements: BoardMeasurements) -> None:
        piece_size = measurements.komadai_piece_size
        self.text_size = measurements.komadai_text_size
        self.koma_size = self.text_size * 3 / 2 if self.is_text else piece_size
        self.vertical_pad = self.text_size / 8 if self.is_text else piece_size / 8
        self.mochigoma_heading_size = 6 * self.text_size  # "▲\n持\n駒\n"

    def _update_origin_and_height(self, num_koma_types: int) -> None:
        self.width: int = komadai_width(self.measurements.komadai_piece_size)
        self.height: int = komadai_height(
            self.mochigoma_heading_size,
            # Actual size of each character in px is about 1.5*text_size
            1.5 * self.text_size,
            num_koma_types,
            self.koma_size,
            self.vertical_pad,
        )
        x_anchor, y_anchor = (
            self.measurements.get_north_komadai_anchor()
            if self.is_north
            else self.measurements.get_south_komadai_anchor()
        )
        self.x_origin: int = int(x_anchor - self.width / 2)
        self.y_origin: int = int(y_anchor if self.is_north else y_anchor - self.height)

    def draw_komadai(self, canvas: BoardCanvas, hand: HandRepresentation) -> None:
        self.hand_counts = {
            ktype: count
            for ktype in HAND_TYPES
            if (count := hand.get_komatype_count(ktype)) > 0
        }
        self._update_origin_and_height(len(self.hand_counts))

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
