from __future__ import annotations

import os
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING
from PIL import Image, ImageTk

import tsumemi.src.tsumemi.img_handlers as imghand
import tsumemi.src.tsumemi.setting_choices as setc

if TYPE_CHECKING:
    from typing import List, Optional


class PieceSkinChoice(setc.Choice[imghand.PieceSkin]):
    pass


PIECE_SKIN_CHOICES: List[PieceSkinChoice] = [
    PieceSkinChoice(skin, skin.desc, skin.name) for skin in imghand.PieceSkin
]


class PieceSkinSelection(setc.Selection[imghand.PieceSkin]):
    pass


class PieceSkinSelectionController:
    def __init__(self) -> None:
        self.model = PieceSkinSelection(PIECE_SKIN_CHOICES)
        return
    
    def make_piece_skin_selection_frame(self, parent: tk.Widget
        ) -> PieceSkinSelectionFrame:
        return PieceSkinSelectionFrame(parent=parent, controller=self)
    
    def get_piece_skin(self) -> imghand.PieceSkin:
        return self.model.get_item()
    
    def get_config_string(self) -> str:
        return self.model.get_config_string()
    
    def select_by_config(self, config_string: str) -> None:
        self.model.select_by_config(config_string)
        return


class PieceSkinDropdown(setc.Dropdown[imghand.PieceSkin]):
    pass


class PieceSkinSelectionFrame(ttk.Frame):
    PREVIEW_WIDTH_HEIGHT = (33, 36)
    def __init__(self,
            parent: tk.Widget,
            controller: PieceSkinSelectionController,
        ) -> None:
        self.controller = controller
        super().__init__(parent)
        self.lbl_name = ttk.Label(self, text="Piece set")
        self.cmb_dropdown = PieceSkinDropdown(parent=self, controller=controller.model)
        # mypy doesn't recognise the "add" parameter overload to bind
        self.cmb_dropdown.bind( # type: ignore
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
    
    def set_preview(self, event: Optional[tk.Event]) -> None:
        skin = self.controller.get_piece_skin()
        filepath = skin.path
        if filepath:
            filename = os.path.join(filepath, "0GI.png")
            img = Image.open(filename).resize(self.PREVIEW_WIDTH_HEIGHT)
            self.lbl_preview["text"] = ""
        else:
            img = Image.new("RGB", self.PREVIEW_WIDTH_HEIGHT, "#FFFFFF")
            self.lbl_preview["text"] = "銀"
        self.preview_photoimage = ImageTk.PhotoImage(img)
        self.lbl_preview["image"] = self.preview_photoimage
        return
