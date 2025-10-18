from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from PIL import Image, ImageTk

from tsumemi.src.tsumemi.skins import BoardSkin

if TYPE_CHECKING:
    from typing import Literal

    ImageKeys = Literal[
        "board_tile", "transparent", "highlight", "highlight2", "semi-transparent"
    ]

logger = logging.getLogger(__name__)

IMG_TRANSPARENT = Image.new("RGBA", (1, 1), "#00000000")
IMG_HIGHLIGHT = Image.new("RGBA", (1, 1), "#99ff0044")
IMG_HIGHLIGHT_2 = Image.new("RGBA", (1, 1), "#3399ff66")
IMG_SEMI_TRANSPARENT = Image.new("RGBA", (1, 1), "#FFFFFF99")


class BoardImageCache:
    def __init__(
        self,
        sq_width: float,
        sq_height: float,
        skin: BoardSkin,
    ) -> None:
        self.skin = skin
        # +1 pixel to avoid gaps when tiling image
        self._sq_width = sq_width + 1
        self._sq_height = sq_height + 1
        self._raws: dict[ImageKeys, Image.Image] = {}
        self._resized: dict[ImageKeys, ImageTk.PhotoImage] = {}
        self._raws["transparent"] = IMG_TRANSPARENT
        self._raws["highlight"] = IMG_HIGHLIGHT
        self._raws["highlight2"] = IMG_HIGHLIGHT_2
        self._raws["semi-transparent"] = IMG_SEMI_TRANSPARENT
        self._load_board_tile_from_skin(skin)

    @property
    def _board_width(self) -> float:
        # Assume 9x9 board; +1 pixel to avoid gaps
        return 9 * self._sq_width + 1

    @property
    def _board_height(self) -> float:
        # Assume 9x9 board; +1 pixel to avoid gaps
        return 9 * self._board_width + 1

    def get_board_image(self) -> ImageTk.PhotoImage | None:
        return self._resized.get("board_tile")

    def get_semi_transparent_board_cover(self) -> ImageTk.PhotoImage | None:
        return self._resized.get("semi-transparent")

    def get_transparent_tile(self) -> ImageTk.PhotoImage | None:
        return self._resized.get("transparent")

    def get_selected_tile_highlight(self) -> ImageTk.PhotoImage | None:
        return self._resized.get("highlight")

    def get_last_move_tile_highlight(self) -> ImageTk.PhotoImage | None:
        return self._resized.get("highlight2")

    def update_dimensions(self, sq_width: float, sq_height: float) -> None:
        # +1 pixel to avoid gaps when tiling image
        self._sq_width = sq_width + 1
        self._sq_height = sq_height + 1
        self._resize_images(
            self._sq_width, self._sq_height, self._board_width, self._board_height
        )

    def _resize_images(
        self, sq_width: float, sq_height: float, board_width: float, board_height: float
    ) -> None:
        for key, raw in self._raws.items():
            match key:
                case "semi-transparent":
                    self._resized[key] = _resize_image(raw, board_width, board_height)
                case _:
                    self._resized[key] = _resize_image(raw, sq_width, sq_height)

    def update_skin(self, skin: BoardSkin) -> None:
        self._load_board_tile_from_skin(skin)
        self.skin = skin

    def _load_board_tile_from_skin(self, skin: BoardSkin) -> None:
        image_filepath = skin.path
        if not image_filepath:
            self.skin = skin
            return
        image = Image.open(image_filepath)
        self._raws["board_tile"] = image
        self._resized["board_tile"] = _resize_image(
            image, self._sq_width, self._sq_height
        )


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
