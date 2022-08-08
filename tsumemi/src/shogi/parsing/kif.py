from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.parsing.base_readers_visitors import GameBuilderPVis
from tsumemi.src.shogi.game import Game
from tsumemi.src.shogi.parsing.kif_reader import KifReader

if TYPE_CHECKING:
    import os
    from typing import Optional, Union
    PathLike = Union[str, os.PathLike]


def read_kif(filepath: PathLike) -> Optional[Game]:
    """Read a KIF file and return the complete game.
    """
    encodings = ["cp932", "utf-8"]
    visitor = GAME_BUILDER_PVIS
    reader = KIF_READER
    game = None
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as _file:
                game = reader.read(_file, visitor)
        except UnicodeDecodeError:
            pass
        else:
            break
    return game


# Since these are essentially just collections of methods a single
# instance suffices for speed. (Actually, are classes even needed for
# polymorphism?)
KIF_READER = KifReader()
GAME_BUILDER_PVIS = GameBuilderPVis()
