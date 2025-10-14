from __future__ import annotations

import os

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generator

    PathLike = str | os.PathLike[str]


def get_kif_files(
    directory: PathLike, recursive: bool
) -> Generator[PathLike, None, None]:
    """
    Returns an generator of full filepaths of KIF files in a given directory.
    """
    yield from (
        _list_kif_files_recursive(directory)
        if recursive
        else _list_kif_files(directory)
    )


def _list_kif_files(directory: PathLike) -> Generator[PathLike, None, None]:
    """
    Returns a generator of full filepaths ending in `.kif` or
    `.kifu` in a directory.
    """
    with os.scandir(directory) as itr:
        yield from (
            os.path.join(directory, entry.name)
            for entry in itr
            if _has_kif_file_extension(entry.name)
        )


def _list_kif_files_recursive(directory: PathLike) -> Generator[PathLike, None, None]:
    """
    Returns a generator of full filepaths ending in `.kif` or
    `.kifu` in a directory and all its subdirectories.
    """
    for dirpath, _, filenames in os.walk(directory):
        yield from (
            os.path.join(dirpath, filename)
            for filename in filenames
            if _has_kif_file_extension(filename)
        )


def _has_kif_file_extension(filename: str) -> bool:
    return filename.endswith(".kif") or filename.endswith(".kifu")
