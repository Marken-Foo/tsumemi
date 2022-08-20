from __future__ import annotations

import os

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple, Union
    PathLike = Union[str, os.PathLike]


BOARD_IMAGES_PATH = os.path.relpath(r"tsumemi/resources/images/boards")
PIECE_IMAGES_PATH = os.path.relpath(r"tsumemi/resources/images/pieces")

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
