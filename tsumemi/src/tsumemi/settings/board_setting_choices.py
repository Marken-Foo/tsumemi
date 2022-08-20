from __future__ import annotations

import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING
from PIL import Image, ImageTk

import tsumemi.src.tsumemi.settings.setting_choices as setc

from tsumemi.src.tsumemi import skins

if TYPE_CHECKING:
    from typing import List, Optional


class BoardSkinChoice(setc.Choice[skins.BoardSkin]):
    pass


BOARD_SKIN_CHOICES: List[BoardSkinChoice] = [
    BoardSkinChoice(skin, skin.desc, skin.name) for skin in skins.BoardSkin
]


class BoardSkinSelection(setc.Selection[skins.BoardSkin]):
    pass


class BoardSkinSelectionController:
    def __init__(self) -> None:
        self.model = BoardSkinSelection(BOARD_SKIN_CHOICES)
        return

    def get_board_skin(self) -> skins.BoardSkin:
        return self.model.get_item()

    def get_config_string(self) -> str:
        return self.model.get_config_string()

    def select_by_config(self, config_string: str) -> None:
        self.model.select_by_config(config_string)
        return


class BoardSkinDropdown(setc.Dropdown[skins.BoardSkin]):
    pass


class BoardSkinSelectionFrame(ttk.Frame):
    PREVIEW_WIDTH_HEIGHT = (33, 36)
    def __init__(self,
            parent: tk.Widget,
            controller: BoardSkinSelectionController,
        ) -> None:
        self.controller = controller
        super().__init__(parent)
        self.lbl_name = ttk.Label(self, text="Board set")
        self.cmb_dropdown = BoardSkinDropdown(parent=self, controller=controller.model)
        self.cmb_dropdown.bind(
            "<<ComboboxSelected>>", self.set_preview, add="+"
        )
        self.preview_photoimage = ImageTk.PhotoImage(
            Image.new("RGBA", self.PREVIEW_WIDTH_HEIGHT, "#000000FF")
        )
        self.lbl_preview = ttk.Label(self, font=("", 18), compound="center")
        self.lbl_preview["image"] = self.preview_photoimage

        self.lbl_name.grid(row=0, column=0, sticky="W")
        self.cmb_dropdown.grid(row=0, column=1)
        self.lbl_preview.grid(row=0, column=2, sticky="E")
        self.set_preview(None)
        return

    def set_preview(self, _event: Optional[tk.Event]) -> None:
        skin = self.controller.get_board_skin()
        filepath = skin.path
        if filepath:
            img = Image.open(filepath).resize(self.PREVIEW_WIDTH_HEIGHT)
        else:
            img = Image.new("RGB", self.PREVIEW_WIDTH_HEIGHT, skin.colour)
        self.preview_photoimage = ImageTk.PhotoImage(img)
        self.lbl_preview["image"] = self.preview_photoimage
        return


class KomadaiSkinSelectionFrame(BoardSkinSelectionFrame):
    def __init__(self,
            parent: tk.Widget,
            controller: BoardSkinSelectionController
        ) -> None:
        super().__init__(parent=parent, controller=controller)
        self.lbl_name["text"] = "Komadai"
        return

    def set_preview(self, _event: Optional[tk.Event]) -> None:
        skin = self.controller.get_board_skin()
        img = Image.new("RGB", self.PREVIEW_WIDTH_HEIGHT, skin.colour)
        self.preview_photoimage = ImageTk.PhotoImage(img)
        self.lbl_preview["image"] = self.preview_photoimage
        return
