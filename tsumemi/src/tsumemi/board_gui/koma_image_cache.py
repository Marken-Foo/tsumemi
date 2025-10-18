from __future__ import annotations

import logging
import os

from typing import TYPE_CHECKING
from PIL import Image, ImageTk

from tsumemi.src.shogi.basetypes import KomaType
from tsumemi.src.tsumemi.board_gui.img_handlers import resize_image

if TYPE_CHECKING:
    from tsumemi.src.tsumemi.skins import PieceSkin

    PathLike = str | os.PathLike[str]

logger = logging.getLogger(__name__)

IMG_HIGHLIGHT = Image.new("RGBA", (1, 1), "#99ff0044")


class KomaImageCache:
    def __init__(self, width: float, height: float, skin: PieceSkin) -> None:
        self.width = width
        self.height = height
        self.skin = skin
        self.raws: dict[str, Image.Image] = {}
        self.resized: dict[str, ImageTk.PhotoImage] = {}
        self.raws["highlight"] = IMG_HIGHLIGHT
        self.resized["highlight"] = resize_image(IMG_HIGHLIGHT, width, height)
        self._load_koma_images_from_skin(skin)

    def _get_key(self, ktype: KomaType, is_upside_down: bool) -> str:
        return f"{1 if is_upside_down else 0}{ktype.to_csa()}"

    def get_highlight_image(self) -> ImageTk.PhotoImage | None:
        return self.resized.get("highlight")

    def get_koma_image(
        self, ktype: KomaType, is_upside_down: bool
    ) -> ImageTk.PhotoImage | None:
        return self.resized.get(self._get_key(ktype, is_upside_down))

    def update_dimensions(self, width: float, height: float) -> None:
        self.width = width
        self.height = height
        self._resize_images(width, height)

    def _resize_images(self, width: float, height: float) -> None:
        for key, raw in self.raws.items():
            self.resized[key] = resize_image(raw, width, height)

    def update_skin(self, skin: PieceSkin) -> None:
        self._load_koma_images_from_skin(skin)
        self.skin = skin

    def _load_koma_images_from_skin(self, skin: PieceSkin) -> None:
        image_directory = skin.path
        if not image_directory:
            self.skin = skin
            return
        for ktype in KomaType:
            if ktype == KomaType.NONE:
                continue
            img_upright = _open_koma_png(image_directory, ktype, is_upside_down=False)
            img_upside_down = _open_koma_png(
                image_directory, ktype, is_upside_down=True
            )
            upright_key = self._get_key(ktype, False)
            upside_down_key = self._get_key(ktype, True)
            self.raws[upright_key] = img_upright
            self.resized[upright_key] = resize_image(
                img_upright, self.width, self.height
            )
            self.raws[upside_down_key] = img_upside_down
            self.resized[upside_down_key] = resize_image(
                img_upside_down, self.width, self.height
            )


def _open_koma_png(
    image_directory: PathLike, ktype: KomaType, is_upside_down: bool
) -> Image.Image:
    """
    Opens koma PNG files as a PIL image. Assumes files are named e.g. `0FU.png`,
    where the first character is `0` (right side up) or `1` (upside down), and
    the koma type is given in all capitals in CSA notation.
    """
    extension = "png"
    filename = f"{1 if is_upside_down else 0}{ktype.to_csa()}.{extension}"
    return Image.open(os.path.join(image_directory, filename))
