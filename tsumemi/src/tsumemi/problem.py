from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from tsumemi.src.tsumemi import timer

if TYPE_CHECKING:
    from os import PathLike
    from typing import Any


class ProblemStatus(Enum):
    NONE = 0
    CORRECT = 1
    WRONG = 2
    SKIP = 3

    def __str__(self) -> str:
        return self.name


class Problem:
    """
    Represents one tsume problem. Identity is based on filepath because
    the problem contents are loaded lazily. Solving statistics (time and status)
    are included but do not affect identity.
    """

    def __init__(self, filepath: PathLike[str]) -> None:
        self.filepath: PathLike[str] = filepath
        self.time: timer.Time | None = None
        self.status: ProblemStatus = ProblemStatus.NONE

    def __eq__(self, obj: Any) -> bool:
        return isinstance(obj, Problem) and self.filepath == obj.filepath
