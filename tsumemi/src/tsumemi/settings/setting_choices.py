from __future__ import annotations

import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from typing import List, Sequence

T = TypeVar('T')


class Choice(Generic[T]):
    def __init__(self, item: T, description: str, config_string: str) -> None:
        self.item = item
        self.description = description
        self.config_string = config_string
        return

    def get_item(self) -> T:
        return self.item


class Selection(Generic[T]):
    def __init__(self, choices: Sequence[Choice[T]]) -> None:
        if not choices:
            raise ValueError("Selection cannot be created from an empty collection")
        self.choices = choices
        self.selected: Choice[T] = choices[0]
        return

    def get_description(self) -> str:
        return self.selected.description

    def get_config_string(self) -> str:
        return self.selected.config_string

    def get_sorted_descriptions(self) -> List[str]:
        return sorted ((choice.description for choice in self.choices))

    def get_item(self) -> T:
        return self.selected.get_item()

    def select_by_description(self, description: str) -> None:
        for choice in self.choices:
            if choice.description == description:
                self.selected = choice
                return
        raise ValueError(f"Description '{description}' not among choices")

    def select_by_config(self, config_string: str) -> None:
        for choice in self.choices:
            if choice.config_string == config_string:
                self.selected = choice
                return
        raise ValueError(f"Config string '{config_string}' not among choices")


class Dropdown(ttk.Combobox, Generic[T]):
    def __init__(self,
            parent: tk.Widget,
            controller: Selection[T],
        ) -> None:
        self.controller = controller
        self._svar = tk.StringVar(value=controller.get_description())
        super().__init__(parent, textvariable=self._svar)
        self["values"] = controller.get_sorted_descriptions()
        self.state(["readonly"])
        self.bind(
            "<<ComboboxSelected>>", self.update_controller, add="+"
        )
        return

    def update_controller(self, event: tk.Event) -> None:
        self.controller.select_by_description(self._svar.get())
        return
