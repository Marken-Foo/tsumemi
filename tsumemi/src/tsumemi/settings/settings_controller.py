from __future__ import annotations

import configparser
import os

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.settings.board_setting_choices as bchoices
import tsumemi.src.tsumemi.settings.notation_setting_choices as nchoices
import tsumemi.src.tsumemi.settings.piece_setting_choices as pchoices

from tsumemi.src.tsumemi import skins
from tsumemi.src.tsumemi.settings.settings_window import SettingsWindow

if TYPE_CHECKING:
    from tsumemi.src.tsumemi.kif_browser_gui import RootController

    PathLike = str | os.PathLike[str]


CONFIG_PATH = os.path.relpath(r"tsumemi/resources/config.ini")


def _default_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config["skins"] = {"pieces": "TEXT", "board": "BROWN", "komadai": "WHITE"}
    config["notation"] = {"notation": "JAPANESE"}
    return config


class Settings:
    # Controller for the settings window.
    def __init__(self, controller: RootController) -> None:
        self.controller = controller
        self.config = configparser.ConfigParser(dict_type=dict)
        self.skin_settings: skins.SkinSettings
        self.notation_controller = nchoices.NotationSelectionController()
        self.board_skin_controller = bchoices.BoardSkinSelectionController()
        self.piece_skin_controller = pchoices.PieceSkinSelectionController()
        self.komadai_skin_controller = bchoices.BoardSkinSelectionController()
        self.read_config_file(CONFIG_PATH)

    def read_config_file(self, filepath: PathLike) -> None:
        try:
            with open(filepath, "r") as f:
                self.config.read_file(f)
        except FileNotFoundError:
            self.config = _default_config()
            with open(filepath, "w") as f:
                self.config.write(f)

        notation_config_string = self.config.get(
            "notation", "notation", fallback="JAPANESE"
        )
        board_config_string = self.config.get("skins", "board", fallback="BROWN")
        komadai_config_string = self.config.get("skins", "komadai", fallback="WHITE")
        piece_config_string = self.config.get("skins", "pieces", fallback="TEXT")

        self.notation_controller.select_by_config(notation_config_string)
        self.board_skin_controller.select_by_config(board_config_string)
        self.komadai_skin_controller.select_by_config(komadai_config_string)
        self.piece_skin_controller.select_by_config(piece_config_string)

    def write_current_settings_to_file(self, filepath: PathLike = CONFIG_PATH) -> None:
        with open(filepath, "w") as f:
            self.config.write(f)

    def push_settings_to_controller(self) -> None:
        skin_settings = self.get_skin_settings()
        move_writer = self.notation_controller.get_move_writer()
        self.controller.apply_skin_settings(skin_settings)
        self.controller.apply_notation_settings(move_writer)

    def get_skin_settings(self) -> skins.SkinSettings:
        piece_skin = self.piece_skin_controller.get_piece_skin()
        board_skin = self.board_skin_controller.get_board_skin()
        komadai_skin = self.komadai_skin_controller.get_board_skin()
        return skins.SkinSettings(piece_skin, board_skin, komadai_skin)

    def update_board_skin_settings(self) -> None:
        if not self.config.has_section("skins"):
            self.config["skins"] = _default_config()["skins"]
        self.config["skins"]["board"] = self.board_skin_controller.get_config_string()

    def update_komadai_skin_settings(self) -> None:
        if not self.config.has_section("skins"):
            self.config["skins"] = _default_config()["skins"]
        self.config["skins"]["komadai"] = (
            self.komadai_skin_controller.get_config_string()
        )

    def update_piece_skin_settings(self) -> None:
        if not self.config.has_section("skins"):
            self.config["skins"] = _default_config()["skins"]
        self.config["skins"]["pieces"] = self.piece_skin_controller.get_config_string()

    def update_notation_settings(self) -> None:
        if not self.config.has_section("notation"):
            self.config["notation"] = _default_config()["notation"]
        self.config["notation"]["notation"] = (
            self.notation_controller.get_config_string()
        )

    def open_settings_window(self) -> None:
        SettingsWindow(controller=self)
