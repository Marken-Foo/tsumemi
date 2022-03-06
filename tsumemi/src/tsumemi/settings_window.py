from __future__ import annotations

import configparser
import os
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING
from PIL import Image, ImageTk

import tsumemi.src.shogi.notation_writer as nwriter
import tsumemi.src.tsumemi.img_handlers as imghand

from tsumemi.src.shogi.basetypes import Koma, Square
from tsumemi.src.shogi.position import Position

if TYPE_CHECKING:
    from typing import Any, Dict, Tuple, Union
    PathLike = Union[str, os.PathLike]


CONFIG_PATH = os.path.relpath(r"tsumemi/resources/config.ini")
CONFIGPARSER = configparser.ConfigParser(dict_type=dict)


def read_config_file(
    ) -> Tuple[imghand.SkinSettings, nwriter.AbstractMoveWriter]:
    """Attempts to read config file; if not found, attempts to write a
    default config file.
    """
    config = CONFIGPARSER
    filepath = CONFIG_PATH
    try:
        with open(filepath, "r") as f:
            config.read_file(f)
    except FileNotFoundError:
        with open(filepath, "w+") as f:
            f.write("[skins]\n")
            f.write("pieces = TEXT\n")
            f.write("board = BROWN\n")
            f.write("komadai = WHITE\n")
            f.write("[notation]\n")
            f.write("notation = JAPANESE\n")
        with open(filepath, "r") as f:
            config.read_file(f)
    
    skins = config["skins"]
    notation = config["notation"]
    return _read_skin(skins), _read_notation(notation)


def _read_skin(skins: configparser.SectionProxy) -> imghand.SkinSettings:
    try:
        piece_skin = imghand.PieceSkin[skins.get("pieces")]
    except KeyError:
        piece_skin = imghand.PieceSkin.TEXT
    try:
        board_skin = imghand.BoardSkin[skins.get("board")]
    except KeyError:
        board_skin = imghand.BoardSkin.WHITE
    try:
        komadai_skin = imghand.BoardSkin[skins.get("komadai")]
    except KeyError:
        komadai_skin = imghand.BoardSkin.WHITE
    return imghand.SkinSettings(piece_skin, board_skin, komadai_skin)


def _read_notation(notation: configparser.SectionProxy
    ) -> nwriter.AbstractMoveWriter:
    try:
        notation_writer = nwriter.MoveWriter[notation.get("notation")]
    except KeyError:
        notation_writer = nwriter.MoveWriter["JAPANESE"]
    return notation_writer.move_writer


class DropdownFromEnum(ttk.Combobox):
    def __init__(self, parent: tk.Widget, src: Any) -> None:
        self.MAPPING_DESC_TO_STRINGKEY: Dict[str, str] = {
            entry.desc: entry.name for entry in src
        }
        self._svar = tk.StringVar(value="")
        super().__init__(parent, textvariable=self._svar)
        self["values"] = list(self.MAPPING_DESC_TO_STRINGKEY.keys())
        self.state(["readonly"])
        return
    
    def get_string_key(self) -> str:
        return self.MAPPING_DESC_TO_STRINGKEY[self._svar.get()]


class NotationDropdown(DropdownFromEnum):
    def get_move_writer(self) -> nwriter.MoveWriter:
        return nwriter.MoveWriter[self.get_string_key()]


class PieceDropdown(DropdownFromEnum):
    def get_piece_skin(self) -> imghand.PieceSkin:
        return imghand.PieceSkin[self.get_string_key()]


class BoardDropdown(DropdownFromEnum):
    def get_board_skin(self) -> imghand.BoardSkin:
        return imghand.BoardSkin[self.get_string_key()]


class NotationSelectionFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, label_text: str) -> None:
        super().__init__(parent)
        self.lbl_name = ttk.Label(self, text=label_text)
        self.cmb_dropdown = NotationDropdown(self, nwriter.MoveWriter)
        self.cmb_dropdown.bind("<<ComboboxSelected>>", self.set_preview)
        self.lbl_preview = ttk.Label(self)
        
        self.lbl_name.grid(row=0, column=0, sticky="W")
        self.cmb_dropdown.grid(row=0, column=1)
        self.lbl_preview.grid(row=0, column=2, sticky="E")
        return
    
    def set_preview(self, event: tk.Event) -> None:
        move_writer = self.cmb_dropdown.get_move_writer()
        self.move_writer = move_writer
        pos = Position()
        pos.set_koma(Koma.FU, Square.from_coord(77))
        move = pos.create_move(Square.from_coord(77), Square.from_coord(76))
        self.lbl_preview["text"] = move_writer.move_writer.get_new_instance().write_move(move, pos)
        return
    
    def get_move_writer(self) -> nwriter.MoveWriter:
        return self.move_writer


class BoardSkinSelectionFrame(ttk.Frame):
    PREVIEW_WIDTH_HEIGHT = (33, 36)
    
    def __init__(self, parent: tk.Widget, label_text: str) -> None:
        super().__init__(parent)
        self.lbl_name = ttk.Label(self, text=label_text)
        self.cmb_dropdown = BoardDropdown(self, imghand.BoardSkin)
        self.cmb_dropdown.bind("<<ComboboxSelected>>", self.set_preview)
        self.preview_photoimage = ImageTk.PhotoImage(
            Image.new("RGBA", self.PREVIEW_WIDTH_HEIGHT, "#000000FF")
        )
        self.lbl_preview = ttk.Label(self)
        self.lbl_preview["image"] = self.preview_photoimage
        
        self.lbl_name.grid(row=0, column=0, sticky="W")
        self.cmb_dropdown.grid(row=0, column=1)
        self.lbl_preview.grid(row=0, column=2, sticky="E")
        return
    
    def set_preview(self, event: tk.Event) -> None:
        skin = self.cmb_dropdown.get_board_skin()
        self.skin = skin
        filepath = skin.path
        if filepath:
            img = Image.open(filepath).resize(self.PREVIEW_WIDTH_HEIGHT)
        else:
            img = Image.new("RGB", self.PREVIEW_WIDTH_HEIGHT, skin.colour)
        self.preview_photoimage = ImageTk.PhotoImage(img)
        self.lbl_preview["image"] = self.preview_photoimage
        return
    
    def get_skin(self) -> imghand.BoardSkin:
        return self.skin


class PieceSkinSelectionFrame(ttk.Frame):
    PREVIEW_WIDTH_HEIGHT = (33, 36)
    
    def __init__(self, parent: tk.Widget, label_text: str) -> None:
        super().__init__(parent)
        self.lbl_name = ttk.Label(self, text=label_text)
        self.cmb_dropdown = PieceDropdown(self, imghand.PieceSkin)
        self.cmb_dropdown.bind("<<ComboboxSelected>>", self.set_preview)
        self.preview_photoimage = ImageTk.PhotoImage(
            Image.new("RGBA", self.PREVIEW_WIDTH_HEIGHT, "#000000FF")
        )
        self.lbl_preview = ttk.Label(self, font=("", 18), compound="center")
        self.lbl_preview["image"] = self.preview_photoimage
        
        self.lbl_name.grid(row=0, column=0, sticky="W")
        self.cmb_dropdown.grid(row=0, column=1)
        self.lbl_preview.grid(row=0, column=2, sticky="E")
        return
    
    def set_preview(self, event: tk.Event) -> None:
        skin = self.cmb_dropdown.get_piece_skin()
        self.skin = skin
        filepath = skin.path
        if filepath:
            filename = os.path.join(skin.path, "0GI.png")
            img = Image.open(filename).resize(self.PREVIEW_WIDTH_HEIGHT)
            self.lbl_preview["text"] = ""
        else:
            img = Image.new("RGB", self.PREVIEW_WIDTH_HEIGHT, "#FFFFFF")
            self.lbl_preview["text"] = "銀"
        self.preview_photoimage = ImageTk.PhotoImage(img)
        self.lbl_preview["image"] = self.preview_photoimage
        return
    
    def get_skin(self) -> imghand.PieceSkin:
        return self.skin


class OptionsFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        
        self.frm_board_options = ttk.LabelFrame(self, text="Board appearance")
        self.frm_board_options.grid(row=0, column=0, sticky="EW")
        self.frm_board_skin = BoardSkinSelectionFrame(self.frm_board_options, "Board")
        self.frm_komadai_skin = BoardSkinSelectionFrame(self.frm_board_options, label_text="Komadai")
        self.frm_piece_skin = PieceSkinSelectionFrame(self.frm_board_options, "Piece set")
        
        self.frm_board_skin.grid(row=0, column=0, sticky="EW")
        self.frm_komadai_skin.grid(row=1, column=0, sticky="EW")
        self.frm_piece_skin.grid(row=2, column=0, sticky="EW")
        
        self.frm_board_skin.grid_columnconfigure(0, weight=1)
        self.frm_komadai_skin.grid_columnconfigure(0, weight=1)
        self.frm_piece_skin.grid_columnconfigure(0, weight=1)
        
        self.frm_notation_options = ttk.LabelFrame(self, text="Notation")
        self.frm_notation_options.grid(row=1, column=0, sticky="EW")
        self.frm_notation_choice = NotationSelectionFrame(self.frm_notation_options, "Notation system")
        
        self.frm_notation_choice.grid(row=0, column=0, sticky="EW")
        self.frm_notation_choice.grid_columnconfigure(0, weight=1)
        return
    
    def get_board_skin(self) -> imghand.BoardSkin:
        return self.frm_board_skin.get_skin()
    
    def get_komadai_skin(self) -> imghand.BoardSkin:
        return self.frm_komadai_skin.get_skin()
    
    def get_piece_skin(self) -> imghand.PieceSkin:
        return self.frm_piece_skin.get_skin()
    
    def get_move_writer(self) -> nwriter.MoveWriter:
        return self.frm_notation_choice.get_move_writer()


class SettingsWindow(tk.Toplevel):
    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(*args, **kwargs)
        
        self.title("Settings")
        
        self.options_frame = OptionsFrame(self)
        self.options_frame.grid(row=0, column=0)
        
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(row=1, column=0, sticky="EW")
        btn_okay = ttk.Button(buttons_frame, text="OK", command=self.save_and_quit)
        btn_okay.grid(row=0, column=0)
        btn_apply = ttk.Button(buttons_frame, text="Apply", command=self.save)
        btn_apply.grid(row=0, column=1)
        return
    
    def save(self):
        with open(CONFIG_PATH, "w") as f:
            # self.controller.config.write(f)
            CONFIGPARSER.write(f)
        # tell the board what skins to use
        piece_skin = self.options_frame.get_piece_skin()
        board_skin = self.options_frame.get_board_skin()
        komadai_skin = self.options_frame.get_komadai_skin()
        skin_settings = imghand.SkinSettings(
            piece_skin, board_skin, komadai_skin
        )
        move_writer = self.options_frame.get_move_writer()
        self.controller.move_writer = move_writer.move_writer.get_new_instance()
        self.controller.apply_skin_settings(skin_settings)
        
        CONFIGPARSER["skins"] = {
            "pieces": piece_skin.name,
            "board": board_skin.name,
            "komadai": komadai_skin.name,
        }
        CONFIGPARSER["notation"] = {
            "notation": move_writer.name
        }
        return
    
    def save_and_quit(self):
        self.save()
        self.destroy()