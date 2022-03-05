from __future__ import annotations

import os
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.shogi.notation_writer as nwriter
import tsumemi.src.tsumemi.img_handlers as imghand

if TYPE_CHECKING:
    from typing import Dict


CONFIG_PATH = os.path.relpath(r"tsumemi/resources/config.ini")


class NotationDropdown(ttk.Combobox):
    MAPPING_DESC_TO_STRINGKEY: Dict[str, str] = {
        "Iroha": "IROHA",
        "Japanese": "JAPANESE",
        "Kitao-Kawasaki": "KITAO-KAWASAKI",
        "Western (numbers)": "WESTERN",
    }
    
    def __init__(self, parent: tk.Widget) -> None:
        self._svar = tk.StringVar(value="Japanese")
        super().__init__(parent, textvariable=self._svar)
        self["values"] = list(self.MAPPING_DESC_TO_STRINGKEY.keys())
        self.state(["readonly"])
        return
    
    def get_string_key(self) -> str:
        return self.MAPPING_DESC_TO_STRINGKEY[self._svar.get()]
    
    def get_move_writer(self) -> nwriter.AbstractMoveWriter:
        return nwriter.MOVE_WRITER[self.get_string_key()]


class PieceDropdown(ttk.Combobox):
    MAPPING_DESC_TO_STRINGKEY: Dict[str, str] = {
        skin.desc: skin.name for skin in imghand.PieceSkin
    }
    
    def __init__(self, parent: tk.Widget) -> None:
        self._svar = tk.StringVar(value="")
        super().__init__(parent, textvariable=self._svar)
        self["values"] = list(self.MAPPING_DESC_TO_STRINGKEY.keys())
        self.state(["readonly"])
        return
    
    def get_string_key(self) -> str:
        return self.MAPPING_DESC_TO_STRINGKEY[self._svar.get()]
    
    def get_piece_skin(self) -> imghand.PieceSkin:
        return imghand.PieceSkin[self.get_string_key()]


class BoardDropdown(ttk.Combobox):
    MAPPING_DESC_TO_STRINGKEY: Dict[str, str] = {
        skin.desc: skin.name for skin in imghand.BoardSkin
    }
    
    def __init__(self, parent: tk.Widget) -> None:
        self._svar = tk.StringVar(value="")
        super().__init__(parent, textvariable=self._svar)
        self["values"] = list(self.MAPPING_DESC_TO_STRINGKEY.keys())
        self.state(["readonly"])
        return
    
    def get_string_key(self) -> str:
        return self.MAPPING_DESC_TO_STRINGKEY[self._svar.get()]
    
    def get_board_skin(self) -> imghand.BoardSkin:
        return imghand.BoardSkin[self.get_string_key()]


class SettingsWindow(tk.Toplevel):
    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(*args, **kwargs)
        
        self.title("Settings")
        
        self.notation_dropdown = NotationDropdown(self)
        self.notation_dropdown.grid(row=0, column=1, sticky="EW")
        
        piece_palette = ttk.LabelFrame(self, text="Piece graphics")
        piece_palette.grid(row=0, column=0, sticky="EW")
        self.piece_dropdown = PieceDropdown(piece_palette)
        self.piece_dropdown.grid(row=0, column=0)
        
        board_palette = ttk.LabelFrame(self, text="Board appearance")
        board_palette.grid(row=1, column=0, sticky="EW")
        ttk.Label(board_palette, text="Board").grid(row=0, column=0, sticky="W")
        ttk.Label(board_palette, text="Komadai (solid colour)").grid(row=0, column=1, sticky="W")
        self.board_dropdown = BoardDropdown(board_palette)
        self.board_dropdown.grid(row=1, column=0, sticky="W")
        self.komadai_dropdown = BoardDropdown(board_palette)
        self.komadai_dropdown.grid(row=1, column=1, sticky="W")
        
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(row=2, column=0, sticky="EW")
        btn_okay = ttk.Button(buttons_frame, text="OK", command=self.save_and_quit)
        btn_okay.grid(row=2, column=0)
        btn_apply = ttk.Button(buttons_frame, text="Apply", command=self.save)
        btn_apply.grid(row=2, column=1)
        return
    
    def save(self):
        self.controller.config["skins"] = {
            "pieces": self.piece_dropdown.get_string_key(),
            "board": self.board_dropdown.get_string_key(),
            "komadai": self.komadai_dropdown.get_string_key(),
        }
        self.controller.move_writer = self.notation_dropdown.get_move_writer()
        self.controller.config["notation"] = {
            "notation": self.notation_dropdown.get_string_key()
        }
        with open(CONFIG_PATH, "w") as f:
            self.controller.config.write(f)
        # tell the board what skins to use
        piece_skin = self.piece_dropdown.get_piece_skin()
        board_skin = self.board_dropdown.get_board_skin()
        komadai_skin = self.komadai_dropdown.get_board_skin()
        skin_settings = imghand.SkinSettings(
            piece_skin, board_skin, komadai_skin
        )
        self.controller.apply_skin_settings(skin_settings)
        return
    
    def save_and_quit(self):
        self.save()
        self.destroy()