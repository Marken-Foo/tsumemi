from __future__ import annotations

import functools
import tkinter as tk

from tkinter import messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from tsumemi.src.tsumemi.kif_browser_gui import RootController


class Menubar(tk.Menu):
    """GUI class for the menubar at the top of the main window."""

    def __init__(
        self, parent: tk.Tk, controller: RootController, *args: Any, **kwargs: Any
    ) -> None:
        self.controller = controller
        super().__init__(parent, *args, **kwargs)

        # Set cascades
        menu_file = tk.Menu(self)
        self.add_cascade(menu=menu_file, label="File")
        menu_solving = tk.Menu(self)
        self.add_cascade(menu=menu_solving, label="Solving")
        menu_settings = tk.Menu(self)
        self.add_cascade(menu=menu_settings, label="Settings")

        # File
        menu_file.add_command(
            label="Open folder...",
            command=self.controller.open_folder,
            accelerator="Ctrl+O",
            underline=0,
        )
        menu_file.add_command(
            label="Open all subfolders...",
            command=self.controller.open_folder_recursive,
            accelerator="Ctrl+Shift+O",
        )
        menu_file.add_separator()
        menu_file.add_command(
            label="Copy SFEN of current position",
            command=self.controller.copy_sfen_to_clipboard,
        )
        # Solving
        menu_solving.add_command(
            label="Get statistics",
            command=self.controller.generate_statistics,
        )
        menu_solving.add_command(
            label="Export results as CSV...",
            command=self.controller.export_prob_list_csv,
        )
        menu_solving.add_separator()
        menu_solving.add_command(
            label="Clear solving statuses",
            command=self.controller.main_problem_list_controller.clear_statuses,
        )
        menu_solving.add_command(
            label="Clear solving times",
            command=self.controller.main_problem_list_controller.clear_times,
        )
        menu_solving.add_command(
            label="Clear results",
            command=self.controller.main_problem_list_controller.clear_results,
        )
        # Settings
        menu_settings.add_command(
            label="Settings...",
            command=self.controller.open_settings_window,
            # command=lambda: SettingsWindow(controller=self.controller.settings),
        )
        menu_settings.add_command(
            label="About tsumemi",
            command=functools.partial(
                messagebox.showinfo,
                title="About tsumemi",
                message="Written in Python 3 by Marken Foo. For the shogi community. KIF files sold separately.",
            ),
        )
        # Bind to main window
        parent["menu"] = self
        return
