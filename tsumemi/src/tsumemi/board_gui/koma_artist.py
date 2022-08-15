from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import KomaType
from tsumemi.src.shogi.basetypes import KANJI_FROM_KTYPE

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from tsumemi.src.tsumemi.board_gui.board_canvas import BoardCanvas
    from tsumemi.src.tsumemi.img_handlers import ImgDict


class AbstractKomaArtist(ABC):
    @abstractmethod
    def draw_koma(self,
            canvas: BoardCanvas,
            x: float,
            y: float,
            ktype: KomaType,
            anchor: str = "center",
            tags: Tuple[str, ...] = ("",),
        ) -> Optional[int]:
        raise NotImplementedError


class ImageKomaArtist(AbstractKomaArtist):
    def __init__(self, koma_dict: ImgDict) -> None:
        self.koma_dict: ImgDict = koma_dict
        return

    def draw_koma(self,
            canvas: BoardCanvas,
            x: float,
            y: float,
            ktype: KomaType,
            anchor: str = "center",
            tags: Tuple[str, ...] = ("",),
        ) -> Optional[int]:
        if ktype == KomaType.NONE:
            return None
        img = self.koma_dict[ktype]
        id_: int
        id_ = canvas.create_image(x, y, image=img, anchor=anchor, tags=tags)
        return id_


class TextKomaArtist(AbstractKomaArtist):
    def __init__(self, canvas: BoardCanvas, invert: bool, komadai: bool
        ) -> None:
        self._text_angle = 180 if invert else 0
        self._text_size = (
            canvas.measurements.komadai_text_size if komadai
            else canvas.measurements.sq_text_size
        )
        return

    def draw_koma(self,
            canvas: BoardCanvas,
            x: float,
            y: float,
            ktype: KomaType,
            anchor: str = "center",
            tags: Tuple[str, ...] = ("",),
        ) -> Optional[int]:
        if ktype == KomaType.NONE:
            return None
        id_: int
        # mypy 0.971 complains no overload variant matches argument types
        id_ = canvas.create_text( # type: ignore
            x, y, text=str(KANJI_FROM_KTYPE[ktype]),
            font=("", self._text_size),
            angle=self._text_angle,
            anchor=anchor, tags=tags
        )
        return id_
