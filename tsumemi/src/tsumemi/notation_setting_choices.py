from __future__ import annotations

import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.shogi.notation_writer as nwriter

from tsumemi.src.shogi.basetypes import Koma, Square
from tsumemi.src.shogi.position import Position

if TYPE_CHECKING:
    from typing import List


class NotationChoice:
    def __init__(self,
            move_writer: nwriter.AbstractMoveWriter,
            description: str,
            config_string: str,
        ) -> None:
        self.move_writer = move_writer
        self.description = description
        self.config_string = config_string # to write to config file
        return
    
    def get_move_writer(self) -> nwriter.AbstractMoveWriter:
        return self.move_writer.get_new_instance()


NOTATION_CHOICES: List[NotationChoice] = [
    NotationChoice(
        nwriter.IrohaMoveWriter(nwriter.JAPANESE_MOVE_FORMAT),
        "Iroha",
        "IROHA",
    ),
    NotationChoice(
        nwriter.JapaneseMoveWriter(nwriter.JAPANESE_MOVE_FORMAT),
        "Japanese",
        "JAPANESE",
    ),
    NotationChoice(
        nwriter.KitaoKawasakiMoveWriter(nwriter.WESTERN_MOVE_FORMAT),
        "Kitao-Kawasaki",
        "KITAO_KAWASAKI",
    ),
    NotationChoice(
        nwriter.WesternMoveWriter(nwriter.WESTERN_MOVE_FORMAT),
        "Western (numbers)",
        "WESTERN",
    ),
]


DEFAULT_NOTATION_CHOICE: NotationChoice = NotationChoice(
    nwriter.JapaneseMoveWriter(nwriter.JAPANESE_MOVE_FORMAT),
    "Japanese (default)",
    "JAPANESE",
)


class NotationSelectionController:
    def __init__(self) -> None:
        self.model = NotationSelection()
        return
    
    def make_notation_selection_frame(self, parent: tk.Widget
        ) -> NotationSelectionFrame:
        return NotationSelectionFrame(parent=parent, controller=self)
    
    def get_move_preview(self) -> str:
        move_writer = self.model.get_selected_move_writer()
        pos = Position()
        pos.set_koma(Koma.FU, Square.from_coord(77))
        move = pos.create_move(Square.from_coord(77), Square.from_coord(76))
        return move_writer.write_move(move, pos)
    
    def get_move_writer(self) -> nwriter.AbstractMoveWriter:
        return self.model.get_selected_move_writer()
    
    def get_move_writer_config_string(self) -> str:
        return self.model.selected.config_string
    
    def set_selection_from_config(self, config_string: str) -> None:
        self.model.update_selection_from_config(config_string)
        return


class NotationSelection:
    def __init__(self, choices: List[NotationChoice] = NOTATION_CHOICES
        ) -> None:
        self.choices: List[NotationChoice]
        self.selected: NotationChoice
        if choices:
            self.choices = choices
            self.selected = choices[0]
        else:
            self.choices = [DEFAULT_NOTATION_CHOICE]
            self.selected = self.choices[0]
        return
    
    def get_current_description(self) -> str:
        return self.selected.description
    
    def get_sorted_descriptions(self) -> List[str]:
        return sorted((choice.description for choice in self.choices))
    
    def get_selected_move_writer(self) -> nwriter.AbstractMoveWriter:
        return self.selected.get_move_writer()
    
    def get_move_writer_from_description(self, description: str
        ) -> nwriter.AbstractMoveWriter:
        for choice in self.choices:
            if choice.description == description:
                self.selected = choice
                return choice.get_move_writer()
        else: # for-else loop
            raise ValueError(f"Description '{description}' not among notation choices")
    
    def get_move_writer_from_config(self, config_string: str
        ) -> nwriter.AbstractMoveWriter:
        for choice in self.choices:
            if choice.config_string == config_string:
                self.selected = choice
                return choice.get_move_writer()
        else: # for-else loop
            raise ValueError(f"Config string '{config_string}' not among notation choices")
    
    def update_selection_from_description(self, description: str) -> None:
        self.get_move_writer_from_description(description)
        return
    
    def update_selection_from_config(self, config_string: str) -> None:
        self.get_move_writer_from_config(config_string)
        return


class NotationSelectionFrame(ttk.Frame):
    def __init__(self,
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
        return
    
    def set_preview(self, event: tk.Event) -> None:
        self.lbl_preview["text"] = self.controller.get_move_preview()
        return


class NotationDropdown(ttk.Combobox):
    def __init__(self,
            parent: tk.Widget,
            controller: NotationSelection,
        ) -> None:
        self.controller = controller
        self._svar = tk.StringVar(value=controller.get_current_description())
        super().__init__(parent, textvariable=self._svar)
        self["values"] = controller.get_sorted_descriptions()
        self.state(["readonly"])
        self.bind("<<ComboboxSelected>>", self.update_controller, add="+")
        return
    
    def update_controller(self, event: tk.Event) -> None:
        self.controller.update_selection_from_description(self._svar.get())
        return
