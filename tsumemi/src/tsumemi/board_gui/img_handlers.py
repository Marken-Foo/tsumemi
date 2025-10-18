from __future__ import annotations

import logging
import os

from abc import ABC
from typing import TYPE_CHECKING
from PIL import Image, ImageTk

from tsumemi.src.shogi.basetypes import KomaType

if TYPE_CHECKING:
    from typing import Any, Callable
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
        self.images[key] = _resize_image(image, self.width, self.height)

    def resize_images(self) -> None:
        """Updates all the resized images by resizing from the stored
        originals.
        """
        for key, raw_img in self.raws.items():
            self.images[key] = _resize_image(raw_img, self.width, self.height)

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


class KomaImgManager(ImgManager):
    """Handles storing and sizing of images for pieces."""

    def __init__(self, measurements: BoardMeasurements, skin: PieceSkin) -> None:
        ImgManager.__init__(self, measurements, skin)

        def _komadai_piece_size() -> tuple[int, int]:
            kpc_w = measurements.komadai_piece_size
            return kpc_w, kpc_w

        def _board_piece_size() -> tuple[float, float]:
            sq_w = measurements.sq_w
            return sq_w, sq_w

        self.imgdicts = {
            "upright": ImgSizingDict(_board_piece_size),
            "inverted": ImgSizingDict(_board_piece_size),
            "komadai_upright": ImgSizingDict(_komadai_piece_size),
            "komadai_inverted": ImgSizingDict(_komadai_piece_size),
        }
        self.skin: PieceSkin
        self.load(skin)

    def load(self, skin: PieceSkin) -> None:
        filepath = skin.path
        if not filepath:
            self.skin = skin
            return
        for ktype in KomaType:
            if ktype == KomaType.NONE:
                continue
            img_upright = _open_koma_png(filepath, ktype, is_upside_down=False)
            img_inverted = _open_koma_png(filepath, ktype, is_upside_down=True)
            self.imgdicts["upright"].add_image(ktype, img_upright)
            self.imgdicts["komadai_upright"].add_image(ktype, img_upright)
            self.imgdicts["inverted"].add_image(ktype, img_inverted)
            self.imgdicts["komadai_inverted"].add_image(ktype, img_inverted)
        self.skin = skin

    def get_dict(self, invert: bool = False, komadai: bool = False) -> ImgSizingDict:
        if not invert and not komadai:
            return self.imgdicts["upright"]
        elif invert and not komadai:
            return self.imgdicts["inverted"]
        elif not invert and komadai:
            return self.imgdicts["komadai_upright"]
        else:  # invert and komadai
            return self.imgdicts["komadai_inverted"]


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


def _resize_image(img: Image.Image, width: float, height: float) -> ImageTk.PhotoImage:
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


class BoardImgManager(ImgManager):
    """Handles storing and sizing of images for the board."""

    def __init__(self, measurements: BoardMeasurements, skin: BoardSkin) -> None:
        ImgManager.__init__(self, measurements, skin)

        def _board_sq_size() -> tuple[float, float]:
            sq_w = measurements.sq_w
            sq_h = measurements.sq_h
            # +1 pixel to avoid gaps when tiling image
            return sq_w + 1, sq_h + 1

        def _board_size() -> tuple[float, float]:
            # for a 9x9 board
            sq_w = measurements.sq_w
            sq_h = measurements.sq_h
            # +1 pixel to avoid gaps
            return 9 * sq_w + 1, 9 * sq_h + 1

        self.imgdicts = {
            "tile_sized": ImgSizingDict(_board_sq_size),
            "board_sized": ImgSizingDict(_board_size),
        }
        self.imgdicts["tile_sized"].add_image("transparent", IMG_TRANSPARENT)
        self.imgdicts["tile_sized"].add_image("highlight", IMG_HIGHLIGHT)
        self.imgdicts["tile_sized"].add_image("highlight2", IMG_HIGHLIGHT_2)
        self.imgdicts["board_sized"].add_image("semi-transparent", IMG_SEMI_TRANSPARENT)
        self.skin: BoardSkin
        self.load(skin)

    def load(self, skin: BoardSkin) -> None:
        filepath = skin.path
        if not filepath:
            # Skin without images
            self.skin = skin
            return
        img = Image.open(filepath)
        self.imgdicts["tile_sized"].add_image("board", img)
        self.skin = skin  # after loading, in case anything goes wrong

    def get_dict(self, board_sized: bool = False) -> ImgSizingDict:
        if board_sized:
            return self.imgdicts["board_sized"]
        return self.imgdicts["tile_sized"]


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
