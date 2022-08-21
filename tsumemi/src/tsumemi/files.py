from __future__ import annotations

import os

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generator, List, Union
    PathLike = Union[str, os.PathLike]


def get_kif_files(directory: PathLike, recursive: bool
    ) -> Generator[PathLike, None, None]:
    """Returns an iterable of full filepaths of KIF files in a
    given directory.
    """
    yield from (_list_kif_files_recursive(directory) if recursive
        else _list_kif_files(directory)
    )

def _list_kif_files(directory: PathLike) -> List[PathLike]:
    """Returns a generator of full filepaths ending in `.kif` or
    `.kifu` in a directory.
    """
    # mypy 0.971 os.scandir() regression
    # https://github.com/python/mypy/issues/11964
    with os.scandir(directory) as itr: # type: ignore
        return [
            os.path.join(directory, entry.name)
            for entry in itr
            if entry.name.endswith(".kif") # type: ignore
            or entry.name.endswith(".kifu") # type: ignore
        ]

def _list_kif_files_recursive(directory: PathLike
    ) -> Generator[PathLike, None, None]:
    """Returns a generator of full filepaths ending in `.kif` or
    `.kifu` in a directory and all its subdirectories.
    """
    for dirpath, _, filenames in os.walk(directory): # type: ignore
        yield from (
            os.path.join(dirpath, filename)
            for filename in filenames
            if filename.endswith(".kif") # type: ignore
            or filename.endswith(".kifu") # type: ignore
        )
