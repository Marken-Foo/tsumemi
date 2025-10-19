from __future__ import annotations

import logging
from PIL import Image, ImageTk


logger = logging.getLogger(__name__)


IMG_TRANSPARENT = Image.new("RGBA", (1, 1), "#00000000")
IMG_HIGHLIGHT = Image.new("RGBA", (1, 1), "#99ff0044")
IMG_HIGHLIGHT_2 = Image.new("RGBA", (1, 1), "#3399ff66")
IMG_SEMI_TRANSPARENT = Image.new("RGBA", (1, 1), "#FFFFFF99")


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
