from __future__ import annotations

import configparser
import os

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.img_handlers as imghand
import tsumemi.src.tsumemi.settings.board_setting_choices as bchoices
import tsumemi.src.tsumemi.settings.notation_setting_choices as nchoices
import tsumemi.src.tsumemi.settings.piece_setting_choices as pchoices

from tsumemi.src.tsumemi.settings.settings_window import SettingsWindow

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


class Settings:
    # Controller for the settings window.
    def __init__(self, controller: RootController) -> None:
        self.controller = controller
        self.config = configparser.ConfigParser(dict_type=dict)
        self.skin_settings: imghand.SkinSettings
        self.notation_controller = nchoices.NotationSelectionController()
        self.board_skin_controller = bchoices.BoardSkinSelectionController()
        self.piece_skin_controller = pchoices.PieceSkinSelectionController()
        self.komadai_skin_controller = bchoices.BoardSkinSelectionController()
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
        try:
            board_config_string = skins_config.get("board")
        except KeyError:
            board_config_string = "WHITE"
        try:
            komadai_config_string = skins_config.get("komadai")
        except KeyError:
            komadai_config_string = "WHITE"
        try:
            piece_config_string = skins_config.get("pieces")
        except KeyError:
            piece_config_string = "TEXT"
        self.notation_controller.select_by_config(notation_config_string)
        self.board_skin_controller.select_by_config(board_config_string)
        self.komadai_skin_controller.select_by_config(komadai_config_string)
        self.piece_skin_controller.select_by_config(piece_config_string)
        return

    def write_current_settings_to_file(self,
            filepath: PathLike = CONFIG_PATH
        ) -> None:
        with open(filepath, "w") as f:
            self.config.write(f)
        return

    def push_settings_to_controller(self) -> None:
        skin_settings = self.get_skin_settings()
        move_writer = self.notation_controller.get_move_writer()
        self.controller.apply_skin_settings(skin_settings)
        self.controller.apply_notation_settings(move_writer)
        return

    def get_skin_settings(self) -> imghand.SkinSettings:
        piece_skin = self.piece_skin_controller.get_piece_skin()
        board_skin = self.board_skin_controller.get_board_skin()
        komadai_skin = self.komadai_skin_controller.get_board_skin()
        return imghand.SkinSettings(piece_skin, board_skin, komadai_skin)

    def update_board_skin_settings(self) -> None:
        self.config["skins"]["board"] = (
            self.board_skin_controller.get_config_string()
        )
        return

    def update_komadai_skin_settings(self) -> None:
        self.config["skins"]["komadai"] = (
            self.komadai_skin_controller.get_config_string()
        )
        return

    def update_piece_skin_settings(self) -> None:
        self.config["skins"]["pieces"] = (
            self.piece_skin_controller.get_config_string()
        )
        return

    def update_notation_settings(self) -> None:
        self.config["notation"]["notation"] = (
            self.notation_controller.get_config_string()
        )
        return

    def open_settings_window(self) -> None:
        SettingsWindow(controller=self)
        return
