from __future__ import annotations

import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.settings.board_setting_choices import BoardSkinSelectionFrame, KomadaiSkinSelectionFrame
from tsumemi.src.tsumemi.settings.notation_setting_choices import NotationSelectionFrame
from tsumemi.src.tsumemi.settings.piece_setting_choices import PieceSkinSelectionFrame

if TYPE_CHECKING:
    from tsumemi.src.tsumemi.settings.settings_controller import Settings


class OptionsFrame(ttk.Frame):
    def __init__(self, parent: SettingsWindow) -> None:
        super().__init__(parent)

        self.frm_board_options = ttk.LabelFrame(self, text="Board appearance")
        self.frm_board_options.grid(row=0, column=0, sticky="EW")
        self.frm_board_skin = BoardSkinSelectionFrame(
            parent=self.frm_board_options,
            controller=parent.controller.board_skin_controller,
        )
        self.frm_komadai_skin = KomadaiSkinSelectionFrame(
            parent=self.frm_board_options,
            controller=parent.controller.komadai_skin_controller,
        )
        self.frm_piece_skin = PieceSkinSelectionFrame(
            parent=self.frm_board_options,
            controller=parent.controller.piece_skin_controller,
        )
        self.frm_board_skin.grid(row=0, column=0, sticky="EW")
        self.frm_komadai_skin.grid(row=1, column=0, sticky="EW")
        self.frm_piece_skin.grid(row=2, column=0, sticky="EW")

        self.frm_board_skin.grid_columnconfigure(0, weight=1)
        self.frm_komadai_skin.grid_columnconfigure(0, weight=1)
        self.frm_piece_skin.grid_columnconfigure(0, weight=1)

        self.frm_notation_options = ttk.LabelFrame(self, text="Notation")
        self.frm_notation_options.grid(row=1, column=0, sticky="EW")
        self.frm_notation_choice = NotationSelectionFrame(
            parent=self.frm_notation_options,
            controller=parent.controller.notation_controller,
        )
        self.frm_notation_choice.grid(row=0, column=0, sticky="EW")
        self.frm_notation_choice.grid_columnconfigure(0, weight=1)
        return


class SettingsWindow(tk.Toplevel):
    def __init__(self, controller: Settings, *args, **kwargs) -> None:
        self.controller = controller
        super().__init__(*args, **kwargs)

        self.title("Settings")

        self.options_frame = OptionsFrame(self)
        self.options_frame.grid(row=0, column=0)

        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(row=1, column=0, sticky="EW")
        btn_okay = ttk.Button(
            buttons_frame, text="OK", command=self.save_and_quit
        )
        btn_okay.grid(row=0, column=0)
        btn_apply = ttk.Button(buttons_frame, text="Apply", command=self.save)
        btn_apply.grid(row=0, column=1)
        return

    def save(self) -> None:
        self.controller.update_board_skin_settings()
        self.controller.update_komadai_skin_settings()
        self.controller.update_piece_skin_settings()
        self.controller.update_notation_settings()
        self.controller.write_current_settings_to_file()
        self.controller.push_settings_to_controller()
        return

    def save_and_quit(self) -> None:
        self.save()
        self.destroy()
