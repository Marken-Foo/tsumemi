from __future__ import annotations

import configparser
import os

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.img_handlers as imghand
import tsumemi.src.tsumemi.notation_setting_choices as nchoices

if TYPE_CHECKING:
    from typing import Union
    from tsumemi.src.tsumemi.kif_browser_gui import RootController
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


class Settings:
    # Controller for the settings window.
    def __init__(self, controller: RootController) -> None:
        self.controller = controller
        self.config = configparser.ConfigParser(dict_type=dict)
        self.skin_settings: imghand.SkinSettings
        self.notation_selection_controller = nchoices.NotationSelectionController()
        
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
        try:
            notation_config_string = notation_config.get("notation")
        except KeyError:
            notation_config_string = "JAPANESE"
        self.skin_settings = _read_skin(skins_config)
        self.notation_selection_controller.set_selection_from_config(notation_config_string)
        return
    
    def write_current_settings_to_file(self,
            filepath: PathLike = CONFIG_PATH
        ) -> None:
        with open(filepath, "w") as f:
            self.config.write(f)
        return
    
    def push_settings_to_controller(self) -> None:
        self.controller.skin_settings = self.skin_settings
        self.controller.move_writer = self.notation_selection_controller.get_move_writer()
        
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
    
    def update_notation_settings(self) -> None:
        self.config["notation"] = {
            "notation": self.notation_selection_controller.get_move_writer_config_string(),
        }
        return
