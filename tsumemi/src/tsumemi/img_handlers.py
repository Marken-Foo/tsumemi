from __future__ import annotations

import logging
import os

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING
from PIL import Image, ImageTk

from tsumemi.src.shogi.basetypes import KomaType

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Tuple, Union
    from tsumemi.src.tsumemi.board_gui.board_meas import BoardMeasurements
    ImgDict = Dict[Any, ImageTk.PhotoImage]
    PathLike = Union[str, os.PathLike]

logger = logging.getLogger(__name__)


BOARD_IMAGES_PATH = os.path.relpath(r"tsumemi/resources/images/boards")
PIECE_IMAGES_PATH = os.path.relpath(r"tsumemi/resources/images/pieces")
IMG_TRANSPARENT = Image.new("RGBA", (1, 1), "#00000000")
IMG_HIGHLIGHT = Image.new("RGBA", (1, 1), "#99ff0066")
IMG_SEMI_TRANSPARENT = Image.new("RGBA", (1, 1), "#FFFFFF99")


class BoardSkin(Enum):
    """Contains names, backup colours, and image paths for boards.
    """
    WHITE = ("solid white", "white", "")
    BROWN = ("solid brown", "#ffd39b", "")
    WOOD1 = ("Wood1", "#d29a00", os.path.join(BOARD_IMAGES_PATH, r"tile_wood1.png"))
    WOOD2 = ("Wood2", "#fbcd77", os.path.join(BOARD_IMAGES_PATH, r"tile_wood2.png"))
    WOOD3 = ("Wood3", "#c98e52", os.path.join(BOARD_IMAGES_PATH, r"tile_wood3.png"))
    WOOD4 = ("Wood4", "#d5b45a", os.path.join(BOARD_IMAGES_PATH, r"tile_wood4.png"))
    WOOD5 = ("Wood5", "#ffdf8f", os.path.join(BOARD_IMAGES_PATH, r"tile_wood5.png"))
    WOOD6 = ("Wood6", "#f4ca64", os.path.join(BOARD_IMAGES_PATH, r"tile_wood6.png"))
    STONE = ("Stone", "#b8b9af", os.path.join(BOARD_IMAGES_PATH, r"tile_stone.png"))
    MILITARY = ("Military", "#a06b3a", os.path.join(BOARD_IMAGES_PATH, r"tile_military.png"))
    MILITARY2 = ("Military2", "#bd7b32", os.path.join(BOARD_IMAGES_PATH, r"tile_military2.png"))

    def __init__(self,
            desc: str, colour: str, path: PathLike
        ) -> None:
        self.desc: str = desc
        self.colour: str = colour
        self.path: PathLike = path


class PieceSkin(Enum):
    """Contains names and image paths for pieces.
    """
    TEXT = ("1-kanji text characters", "")
    LIGHT = ("1-kanji light pieces", os.path.join(PIECE_IMAGES_PATH, r"kanji_light"))
    BROWN = ("1-kanji brown pieces", os.path.join(PIECE_IMAGES_PATH, r"kanji_brown"))
    REDWOOD = ("1-kanji red wood pieces", os.path.join(PIECE_IMAGES_PATH, r"kanji_red_wood"))
    INTL = ("Internationalised symbols", os.path.join(PIECE_IMAGES_PATH, r"international"))
    TOMATO_COLOURED = ("CouchTomato internationalised symbols", os.path.join(PIECE_IMAGES_PATH, r"tomato_colored"))
    TOMATO_MONOCHROME = ("CouchTomato internationalised symbols (single colour)", os.path.join(PIECE_IMAGES_PATH, r"tomato_monochrome"))

    def __init__(self, desc: str, path: PathLike) -> None:
        self.desc: str = desc
        self.path: PathLike = path
        return


class SkinSettings:
    """Contains a set of skins needed to draw a board.
    """
    def __init__(self,
            piece_skin: PieceSkin,
            board_skin: BoardSkin,
            komadai_skin: BoardSkin,
        ) -> None:
        self.piece_skin = piece_skin
        self.board_skin = board_skin
        self.komadai_skin = komadai_skin
        return

    def get(self) -> Tuple[PieceSkin, BoardSkin, BoardSkin]:
        return self.piece_skin, self.board_skin, self.komadai_skin


class ImgSizingDict:
    """Take PIL Image and store it alongside a resized
    ImageTk.PhotoImage. Manage resized dimensions via function passed
    in constructor. Responsible for resizing images to correct
    dimensions.
    """
    def __init__(self, update_func: Callable[[], Tuple[int, int]]) -> None:
        """Create ImgSizingDict. update_func is a function returning
        tuple (width, height) of the desired dimensions of the stored
        images.
        """
        self.update_func = update_func
        self.width, self.height = update_func()
        self.raws: Dict[Union[str, KomaType], Image.Image] = {}
        self.images: ImgDict = {}
        return

    def _resize_image(self, img, width: int, height: int) -> ImageTk.PhotoImage:
        """Take PIL Image img, return resized ImageTk.PhotoImage.
        """
        try:
            resized_img = img.resize((int(width), int(height)))
        except ValueError:
            logger.info("Image resizing in ImgDict failed, passed parameters width %i, height %i", int(width), int(height))
            return ImageTk.PhotoImage(Image.new("RGB", (1, 1), "#000000"))
        return ImageTk.PhotoImage(resized_img)

    def add_image(self, key: Union[str, KomaType], image: Image.Image) -> None:
        self.raws[key] = image
        self.images[key] = self._resize_image(image, self.width, self.height)
        return

    def resize_images(self) -> None:
        for key, raw_img in self.raws.items():
            self.images[key] = self._resize_image(
                raw_img, self.width, self.height
            )
        return

    def update_sizes(self) -> None:
        self.width, self.height = self.update_func()
        return

    def get_dict(self) -> ImgDict:
        return self.images


class ImgManager(ABC):
    def __init__(self,
            measurements: BoardMeasurements,
            skin: Union[BoardSkin, PieceSkin],
        ) -> None:
        self.measurements = measurements
        self.skin = skin
        return

    def has_images(self) -> bool:
        return bool(self.skin.path)

    @abstractmethod
    def load(self, skin):
        pass

    @abstractmethod
    def resize_images(self):
        pass


class KomaImgManager(ImgManager):
    """Handles storing and sizing of images for pieces.
    """
    def __init__(self,
            measurements: BoardMeasurements, skin: PieceSkin
        ) -> None:
        super().__init__(measurements, skin)
        def _komadai_piece_size() -> Tuple[int, int]:
            kpc_w = measurements.komadai_piece_size
            return kpc_w, kpc_w
        def _board_piece_size() -> Tuple[int, int]:
            sq_w = int(measurements.sq_w)
            return sq_w, sq_w
        self.upright = ImgSizingDict(_board_piece_size)
        self.inverted = ImgSizingDict(_board_piece_size)
        self.komadai_upright = ImgSizingDict(_komadai_piece_size)
        self.komadai_inverted = ImgSizingDict(_komadai_piece_size)
        self.skin: PieceSkin
        self.load(skin)
        return

    def load(self, skin: PieceSkin) -> None:
        filepath = skin.path
        if filepath:
            for ktype in KomaType:
                if ktype == KomaType.NONE:
                    continue
                filename = "0" + ktype.to_csa() + ".png"
                img_path = os.path.join(filepath, filename)
                img = Image.open(img_path)
                self.upright.add_image(ktype, img)
                self.komadai_upright.add_image(ktype, img)
                # upside-down image
                filename = "1" + ktype.to_csa() + ".png"
                img_path = os.path.join(filepath, filename)
                img = Image.open(img_path)
                self.inverted.add_image(ktype, img)
                self.komadai_inverted.add_image(ktype, img)
            self.skin = skin
            return
        else:
            # skin without images
            self.skin = skin
            return

    def resize_images(self) -> None:
        if self.skin.path:
            imgdicts = (
                self.upright,
                self.inverted,
                self.komadai_upright,
                self.komadai_inverted
            )
            for imgdict in imgdicts:
                imgdict.update_sizes()
                imgdict.resize_images()
        return

    def get_dict(self, invert=False, komadai=False) -> ImgDict:
        if not invert and not komadai:
            return self.upright.get_dict()
        elif invert and not komadai:
            return self.inverted.get_dict()
        elif not invert and komadai:
            return self.komadai_upright.get_dict()
        else: # invert and komadai
            return self.komadai_inverted.get_dict()


class BoardImgManager(ImgManager):
    """Handles storing and sizing of images for the board.
    """
    def __init__(self,
            measurements: BoardMeasurements, skin: BoardSkin
        ) -> None:
        super().__init__(measurements, skin)
        def _board_sq_size():
            sq_w = measurements.sq_w
            sq_h = measurements.sq_h
            # +1 pixel to avoid gaps when tiling image
            return sq_w+1, sq_h+1
        def _board_size():
            # for a 9x9 board
            sq_w = measurements.sq_w
            sq_h = measurements.sq_h
            # +1 pixel to avoid gaps
            return 9*sq_w+1, 9*sq_h+1
        # Populate default images
        self.tile_sized = ImgSizingDict(_board_sq_size)
        self.tile_sized.add_image("transparent", IMG_TRANSPARENT)
        self.tile_sized.add_image("highlight", IMG_HIGHLIGHT)
        self.board_sized = ImgSizingDict(_board_size)
        self.board_sized.add_image("semi-transparent", IMG_SEMI_TRANSPARENT)
        self.skin: BoardSkin
        self.load(skin)
        return

    def load(self, skin: BoardSkin) -> None:
        filepath = skin.path
        if filepath:
            img = Image.open(filepath)
            self.tile_sized.add_image("board", img)
            self.skin = skin # after loading, in case anything goes wrong
            return
        else:
            # skin without images
            self.skin = skin
            return

    def resize_images(self) -> None:
        if self.skin.path:
            imgdicts = (self.tile_sized, self.board_sized)
            for imgdict in imgdicts:
                imgdict.update_sizes()
                imgdict.resize_images()
        return

    def get_dict(self, board_sized: bool = False) -> ImgDict:
        if board_sized:
            return self.board_sized.get_dict()
        else:
            return self.tile_sized.get_dict()


class KomadaiImgManager(ImgManager):
    """Handles storing and sizing of images for the komadai.
    """
    def __init__(self,
            measurements: BoardMeasurements, skin: BoardSkin
        ) -> None:
        super().__init__(measurements, skin)
        def _komadai_piece_size() -> Tuple[int, int]:
            kpc_w = measurements.komadai_piece_size
            return kpc_w, kpc_w
        # Populate default images
        self.komadai_piece_sized = ImgSizingDict(_komadai_piece_size)
        self.komadai_piece_sized.add_image(
            "highlight", IMG_HIGHLIGHT
        )
        return

    def load(self, skin: BoardSkin) -> None:
        self.skin = skin
        return

    def resize_images(self) -> None:
        if self.skin.path:
            imgdicts = (self.komadai_piece_sized,)
            for imgdict in imgdicts:
                imgdict.update_sizes()
                imgdict.resize_images()
        return

    def get_dict(self) -> ImgDict:
        return self.komadai_piece_sized.get_dict()
