from __future__ import annotations

import functools
import itertools

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import Koma, Side
from tsumemi.src.shogi.position_internals import Dir

if TYPE_CHECKING:
    from typing import Callable, Iterable, Generator
    from tsumemi.src.shogi.position_internals import MailboxBoard
    Steps = Generator[int, None, None]
    IdxIterable = Iterable[int]
    DestIdxGenerator = Callable[..., IdxIterable]

def _forward(side: Side) -> Dir:
    return Dir.S if side == Side.GOTE else Dir.N

def steps_fu(start_idx: int, side: Side) -> Steps:
    forward = _forward(side)
    yield start_idx+forward

def steps_ke(start_idx: int, side: Side) -> Steps:
    forward = _forward(side)
    yield from (
        start_idx+forward+forward+Dir.E,
        start_idx+forward+forward+Dir.W
    )

def steps_gi(start_idx: int, side: Side) -> Steps:
    forward = _forward(side)
    yield from (
        start_idx+forward, start_idx+Dir.NE, start_idx+Dir.SE,
        start_idx+Dir.SW, start_idx+Dir.NW
    )

def steps_ki(start_idx: int, side: Side) -> Steps:
    forward = _forward(side)
    yield from (
        start_idx+Dir.N, start_idx+Dir.S, start_idx+Dir.E, start_idx+Dir.W,
        start_idx+forward+Dir.E, start_idx+forward+Dir.W
    )

def steps_ou(start_idx: int, side: Side) -> Steps:
    yield from (
        start_idx+Dir.N, start_idx+Dir.NE, start_idx+Dir.E,
        start_idx+Dir.SE, start_idx+Dir.S, start_idx+Dir.SW,
        start_idx+Dir.W, start_idx+Dir.NW
    )

def filter_for_valid_dests(
        dest_idx_generator: DestIdxGenerator
    ) -> DestIdxGenerator:
    @functools.wraps(dest_idx_generator)
    def wrapper_filter_for_valid_dests(
            board: MailboxBoard, start_idx: int, side: Side,
            *args, **kwargs
        ) -> IdxIterable:
        dest_idxs = dest_idx_generator(
            board=board, start_idx=start_idx, side=side, *args, **kwargs
        )
        return (idx for idx in dest_idxs if board.mailbox[idx] != Koma.INVALID)
    return wrapper_filter_for_valid_dests

def _generate_line_idxs(
        board: MailboxBoard, side: Side, start_idx: int, dir: Dir
    ) -> IdxIterable:
    """Generate destination square indices, assuming koma at location
    start_idx moving in a line along direction dir.
    """
    dest = start_idx + dir
    dest_koma = board.mailbox[dest]
    while dest_koma == Koma.NONE:
        yield dest
        dest += dir
        dest_koma = board.mailbox[dest]
    if dest_koma != Koma.INVALID and dest_koma.side() != side:
        yield(dest)

@filter_for_valid_dests
def generate_dests_steps(
        board: MailboxBoard, start_idx: int, side: Side,
        steps: Callable[[int, Side], Steps]
    ) -> IdxIterable:
    for dest in steps(start_idx, side):
        target_koma = board.mailbox[dest]
        is_valid_dest = (
            (target_koma != Koma.INVALID)
            and (target_koma == Koma.NONE or target_koma.side() != side)
        )
        if is_valid_dest:
            yield dest

@filter_for_valid_dests
def generate_dests_ky(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> IdxIterable:
    forward = _forward(side)
    return _generate_line_idxs(board, side, start_idx, forward)

@filter_for_valid_dests
def generate_dests_ka(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> IdxIterable:
    ne = _generate_line_idxs(board, side, start_idx, Dir.NE)
    se = _generate_line_idxs(board, side, start_idx, Dir.SE)
    nw = _generate_line_idxs(board, side, start_idx, Dir.NW)
    sw = _generate_line_idxs(board, side, start_idx, Dir.SW)
    return itertools.chain(ne, se, nw, sw)

@filter_for_valid_dests
def generate_dests_hi(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> IdxIterable:
    n = _generate_line_idxs(board, side, start_idx, Dir.N)
    s = _generate_line_idxs(board, side, start_idx, Dir.S)
    e = _generate_line_idxs(board, side, start_idx, Dir.E)
    w = _generate_line_idxs(board, side, start_idx, Dir.W)
    return itertools.chain(n, s, e, w)

@filter_for_valid_dests
def generate_dests_um(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> IdxIterable:
    # mypy __wrapped__ issue: https://github.com/python/typeshed/issues/4826
    kaku = generate_dests_ka.__wrapped__(board, start_idx, side) # type: ignore
    wazir = (
        start_idx+Dir.N, start_idx+Dir.S,
        start_idx+Dir.E, start_idx+Dir.W
    )
    return itertools.chain(kaku, wazir)

@filter_for_valid_dests
def generate_dests_ry(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> IdxIterable:
    # mypy __wrapped__ issue: https://github.com/python/typeshed/issues/4826
    hisha = generate_dests_hi.__wrapped__(board, start_idx, side) # type: ignore
    alfil = (
        start_idx+Dir.NE, start_idx+Dir.SE,
        start_idx+Dir.SW, start_idx+Dir.NW
    )
    return itertools.chain(hisha, alfil)
