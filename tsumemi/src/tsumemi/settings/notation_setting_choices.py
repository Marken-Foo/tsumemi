from __future__ import annotations

import tkinter as tk

from tkinter import ttk

import tsumemi.src.tsumemi.settings.setting_choices as setc

from tsumemi.src.shogi.notation import (
    AbstractMoveWriter,
    IrohaMoveWriter,
    JapaneseMoveWriter,
    KitaoKawasakiMoveWriter,
    WesternMoveWriter,
)
from tsumemi.src.shogi.basetypes import Koma
from tsumemi.src.shogi.position import Position
from tsumemi.src.shogi.square import Square


class NotationChoice(setc.Choice[AbstractMoveWriter]):
    pass


NOTATION_CHOICES: list[NotationChoice] = [
    NotationChoice(
        IrohaMoveWriter(),
        "Iroha",
        "IROHA",
    ),
    NotationChoice(
        JapaneseMoveWriter(),
        "Japanese",
        "JAPANESE",
    ),
    NotationChoice(
        KitaoKawasakiMoveWriter(),
        "Kitao-Kawasaki",
        "KITAO_KAWASAKI",
    ),
    NotationChoice(
        WesternMoveWriter(),
        "Western (numbers)",
        "WESTERN",
    ),
]


class NotationSelection(setc.Selection[AbstractMoveWriter]):
    pass


class NotationSelectionController:
    def __init__(self) -> None:
        self.model = NotationSelection(NOTATION_CHOICES)
        return

    def get_move_preview(self) -> str:
        move_writer = self.model.get_item()
        pos = Position()
        pos.set_koma(Koma.FU, Square.from_coord(77))
        move = pos.create_move(Square.from_coord(77), Square.from_coord(76))
        return move_writer.write_move(move, pos)

    def get_move_writer(self) -> AbstractMoveWriter:
        return self.model.get_item()

    def get_config_string(self) -> str:
        return self.model.get_config_string()

    def select_by_config(self, config_string: str) -> None:
        self.model.select_by_config(config_string)
        return


class NotationDropdown(setc.Dropdown[AbstractMoveWriter]):
    pass


class NotationSelectionFrame(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        controller: NotationSelectionController,
    ) -> None:
        self.controller = controller
        super().__init__(parent)
        self.lbl_name = ttk.Label(self, text="Notation system")
        self.cmb_dropdown = NotationDropdown(parent=self, controller=controller.model)
        self.cmb_dropdown.bind("<<ComboboxSelected>>", self.set_preview, add="+")
        self.lbl_preview = ttk.Label(self)

        self.lbl_name.grid(row=0, column=0, sticky="W")
        self.cmb_dropdown.grid(row=0, column=1)
        self.lbl_preview.grid(row=0, column=2, sticky="E")
        self.set_preview(None)
        return

    def set_preview(self, event: tk.Event | None) -> None:
        self.lbl_preview["text"] = self.controller.get_move_preview()
        return
