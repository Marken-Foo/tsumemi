from __future__ import annotations

import configparser
import os

from typing import TYPE_CHECKING

import tsumemi.src.shogi.notation_writer as nwriter
import tsumemi.src.tsumemi.img_handlers as imghand

if TYPE_CHECKING:
    from typing import Any, Union
    PathLike = Union[str, os.PathLike]


CONFIG_PATH = os.path.relpath(r"tsumemi/resources/config.ini")


def write_default_config_file(filepath: PathLike) -> None:
    with open(filepath, "w+") as f:
        f.write("[skins]\n")
        f.write("pieces = TEXT\n")
        f.write("board = BROWN\n")
        f.write("komadai = WHITE\n")
        f.write("[notation]\n")
        f.write("notation = JAPANESE\n")
    return


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


class Settings:
    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.config = configparser.ConfigParser(dict_type=dict)
        self.skin_settings: imghand.SkinSettings
        self.move_writer: nwriter.AbstractMoveWriter
        self.read_config_file(CONFIG_PATH)
        return
    
    def read_config_file(self, filepath: PathLike) -> None:
        try:
            with open(filepath, "r") as f:
                self.config.read_file(f)
        except FileNotFoundError:
            write_default_config_file(filepath)
            with open(filepath, "r") as f:
                self.config.read_file(f)
        
        skins_config = self.config["skins"]
        notation_config = self.config["notation"]
        
        self.skin_settings = _read_skin(skins_config)
        self.move_writer = _read_notation(notation_config)
        return
    
    def write_current_settings_to_file(self,
            filepath: PathLike = CONFIG_PATH
        ) -> None:
        with open(filepath, "w") as f:
            self.config.write(f)
        return
    
    def push_settings_to_controller(self) -> None:
        self.controller.skin_settings = self.skin_settings
        self.controller.move_writer = self.move_writer
        self.controller.apply_skin_settings(self.skin_settings)
        return
    
    def update_skin_settings(self, skin_settings: imghand.SkinSettings) -> None:
        piece_skin, board_skin, komadai_skin = skin_settings.get()
        self.skin_settings = skin_settings
        self.config["skins"] = {
            "pieces": piece_skin.name,
            "board": board_skin.name,
            "komadai": komadai_skin.name,
        }
        return
    
    def update_notation_settings(self, move_writer: nwriter.MoveWriter) -> None:
        self.move_writer = move_writer.move_writer.get_new_instance()
        self.config["notation"] = {
            "notation": move_writer.name,
        }
        return
