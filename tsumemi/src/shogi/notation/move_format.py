from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi import rules

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from tsumemi.src.shogi.move import Move
    from tsumemi.src.shogi.notation.abstract_move_writer import AbstractMoveWriter
    from tsumemi.src.shogi.position import Position

    MoveNotationBuilder = Callable[[Move, Position, "AbstractMoveWriter"], str]
    MoveFormat = Iterable["MoveNotationBuilder"]


def _write_koma(move: Move, _pos: Position, move_writer: AbstractMoveWriter) -> str:
    """MoveNotationBuilder function."""
    return move_writer.write_koma(move.koma)


def _write_disambiguation(
    move: Move, pos: Position, move_writer: AbstractMoveWriter
) -> str:
    """MoveNotationBuilder function."""
    ambiguous_moves = rules.get_ambiguous_moves(pos, move)
    needs_disambiguation = move_writer.needs_disambiguation(move, ambiguous_moves)
    if not needs_disambiguation:
        return ""
    return move_writer.write_disambiguation(move, ambiguous_moves)


def _write_movetype(move: Move, _pos: Position, move_writer: AbstractMoveWriter) -> str:
    """MoveNotationBuilder function. Writes whether a move is a drop,
    capture, or normal move.
    """
    return move_writer.write_movetype(move)


def _write_destination(
    move: Move, _pos: Position, move_writer: AbstractMoveWriter
) -> str:
    """MoveNotationBuilder function."""
    return move_writer.write_destination(move.end_sq)


def _write_same_destination(
    move: Move, _pos: Position, move_writer: AbstractMoveWriter
) -> str:
    """MoveNotationBuilder function."""
    return move_writer.write_same_destination(move.end_sq)


def _write_promotion(
    move: Move, _pos: Position, move_writer: AbstractMoveWriter
) -> str:
    """MoveNotationBuilder function."""
    if rules.can_be_promotion(move):
        return move_writer.write_promotion(move.is_promotion)
    return ""


WESTERN_MOVE_FORMAT: MoveFormat = (
    _write_koma,
    _write_disambiguation,
    _write_movetype,
    _write_destination,
    _write_promotion,
)


JAPANESE_MOVE_FORMAT: MoveFormat = (
    _write_destination,
    _write_koma,
    _write_movetype,
    _write_disambiguation,
    _write_promotion,
)


def with_same_destination(move_format: MoveFormat) -> MoveFormat:
    return tuple(
        _write_same_destination if func is _write_destination else func
        for func in move_format
    )
