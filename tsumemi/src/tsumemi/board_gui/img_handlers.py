from __future__ import annotations

import logging
import os

from abc import ABC
from typing import TYPE_CHECKING
from PIL import Image, ImageTk


if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any
    from tsumemi.src.shogi.basetypes import KomaType
    from tsumemi.src.tsumemi.skins import BoardSkin, PieceSkin
    from tsumemi.src.tsumemi.board_gui.board_meas import BoardMeasurements

    PathLike = str | os.PathLike[str]

logger = logging.getLogger(__name__)


IMG_TRANSPARENT = Image.new("RGBA", (1, 1), "#00000000")
IMG_HIGHLIGHT = Image.new("RGBA", (1, 1), "#99ff0044")
IMG_HIGHLIGHT_2 = Image.new("RGBA", (1, 1), "#3399ff66")
IMG_SEMI_TRANSPARENT = Image.new("RGBA", (1, 1), "#FFFFFF99")


class ImgSizingDict:
    """Stores PIL images and their resized versions. This keeps
    references to the images so they will not be garbage-collected,
    and also allows resizing on the fly.
    """

    def __init__(self, update_func: Callable[[], tuple[float, float]]) -> None:
        """Create ImgSizingDict. `update_func` is a Callable
        returning a tuple of the `(width, height)` that the resized
        images should be.
        """
        self.update_func = update_func
        self.width, self.height = map(int, update_func())
        self.raws: dict[str | KomaType, Image.Image] = {}
        self.images: dict[Any, ImageTk.PhotoImage] = {}

    def __getitem__(self, key: Any) -> ImageTk.PhotoImage:
        return self.images[key]

    def add_image(self, key: str | KomaType, image: Image.Image) -> None:
        """Stores the PIL Image as well as a resized copy."""
        self.raws[key] = image
        self.images[key] = resize_image(image, self.width, self.height)

    def resize_images(self) -> None:
        """Updates all the resized images by resizing from the stored
        originals.
        """
        for key, raw_img in self.raws.items():
            self.images[key] = resize_image(raw_img, self.width, self.height)

    def update_sizes(self) -> None:
        self.width, self.height = map(int, self.update_func())


class ImgManager(ABC):
    def __init__(
        self,
        measurements: BoardMeasurements,
        skin: BoardSkin | PieceSkin,
    ) -> None:
        self.measurements = measurements
        self.skin = skin
        self.imgdicts: dict[str, ImgSizingDict]

    def has_images(self) -> bool:
        return bool(self.skin.path)

    def resize_images(self) -> None:
        if not self.skin.path:
            return
        for imgdict in self.imgdicts.values():
            imgdict.update_sizes()
            imgdict.resize_images()


def resize_image(img: Image.Image, width: float, height: float) -> ImageTk.PhotoImage:
    """
    Returns a resized `ImageTk.PhotoImage` from a PIL `Image` and desired width and height.
    """
    try:
        resized_img = img.resize((int(width), int(height)))
        return ImageTk.PhotoImage(resized_img)
    except ValueError:
        logger.info(
            f"Failed to resize image to dimensions {int(width)} * {int(height)}."
        )
        return ImageTk.PhotoImage(Image.new("RGB", (1, 1), "#000000"))


class KomadaiImgManager(ImgManager):
    """Handles storing and sizing of images for the komadai."""

    def __init__(self, measurements: BoardMeasurements, skin: BoardSkin) -> None:
        ImgManager.__init__(self, measurements, skin)

        def _komadai_piece_size() -> tuple[int, int]:
            kpc_w = measurements.komadai_piece_size
            return kpc_w, kpc_w

        self.imgdicts = {
            "komadai_piece_sized": ImgSizingDict(_komadai_piece_size),
        }
        self.imgdicts["komadai_piece_sized"].add_image("highlight", IMG_HIGHLIGHT)

    def load(self, skin: BoardSkin) -> None:
        self.skin = skin

    def get_dict(self) -> ImgSizingDict:
        return self.imgdicts["komadai_piece_sized"]
