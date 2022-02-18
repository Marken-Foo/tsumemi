from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.shogi.basetypes import Koma, Side
from tsumemi.src.shogi.position_internals import Dir

if TYPE_CHECKING:
    from typing import Callable, List, Tuple
    from tsumemi.src.shogi.position_internals import MailboxBoard
    Steps = Tuple[int, ...]


def steps_fu(start_idx: int, side: Side) -> Steps:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return (start_idx+forward,)

def steps_ke(start_idx: int, side: Side) -> Steps:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return (
        start_idx+forward+forward+Dir.E,
        start_idx+forward+forward+Dir.W
    )

def steps_gi(start_idx: int, side: Side) -> Steps:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return (
        start_idx+forward, start_idx+Dir.NE, start_idx+Dir.SE,
        start_idx+Dir.SW, start_idx+Dir.NW
    )

def steps_ki(start_idx: int, side: Side) -> Steps:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return (
        start_idx+Dir.N, start_idx+Dir.S, start_idx+Dir.E, start_idx+Dir.W,
        start_idx+forward+Dir.E, start_idx+forward+Dir.W
    )

def steps_ou(start_idx: int, side: Side) -> Steps:
    return (
        start_idx+Dir.N, start_idx+Dir.NE, start_idx+Dir.E,
        start_idx+Dir.SE, start_idx+Dir.S, start_idx+Dir.SW,
        start_idx+Dir.W, start_idx+Dir.NW
    )

def filter_for_valid_dests(
        dest_idx_list: List[int],
        board: MailboxBoard
    ) -> List[int]:
    return [idx for idx in dest_idx_list if board.mailbox[idx] != Koma.INVALID]

def _generate_line_idxs(
        board: MailboxBoard, side: Side, start_idx: int, dir: Dir
    ) -> List[int]:
    """Generate a list of target destination square indices,
    assuming a koma at location start_idx that moves in a line
    along the direction dir.
    """
    res = []
    dest = start_idx + dir
    dest_koma = board.mailbox[dest]
    while dest_koma == Koma.NONE:
        res.append(dest)
        dest += dir
        dest_koma = board.mailbox[dest]
    if dest_koma != Koma.INVALID and dest_koma.side() != side:
        res.append(dest)
    return res

def generate_dests_steps(
        board: MailboxBoard, start_idx: int, side: Side,
        steps: Callable[[int, Side], Steps]
    ) -> List[int]:
    res = []
    targets = steps(start_idx, side)
    for target in targets:
        target_koma = board.mailbox[target]
        is_valid_target = (
            (target_koma != Koma.INVALID)
            and (target_koma == Koma.NONE or target_koma.side() != side)
        )
        if is_valid_target:
            res.append(target)
    return res

def generate_dests_ky(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> List[int]:
    forward = Dir.S if side == Side.GOTE else Dir.N
    return _generate_line_idxs(board, side, start_idx, forward)

def generate_dests_ka(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> List[int]:
    ne = _generate_line_idxs(board, side, start_idx, Dir.NE)
    se = _generate_line_idxs(board, side, start_idx, Dir.SE)
    nw = _generate_line_idxs(board, side, start_idx, Dir.NW)
    sw = _generate_line_idxs(board, side, start_idx, Dir.SW)
    return ne + se + nw + sw

def generate_dests_hi(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> List[int]:
    n = _generate_line_idxs(board, side, start_idx, Dir.N)
    s = _generate_line_idxs(board, side, start_idx, Dir.S)
    e = _generate_line_idxs(board, side, start_idx, Dir.E)
    w = _generate_line_idxs(board, side, start_idx, Dir.W)
    return n + s + e + w

def generate_dests_um(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> List[int]:
    kaku = generate_dests_ka(board, start_idx, side)
    wazir = [
        start_idx+Dir.N, start_idx+Dir.S,
        start_idx+Dir.E, start_idx+Dir.W
    ]
    return kaku + wazir

def generate_dests_ry(
        board: MailboxBoard, start_idx: int, side: Side
    ) -> List[int]:
    hisha = generate_dests_hi(board, start_idx, side)
    alfil = [
        start_idx+Dir.NE, start_idx+Dir.SE,
        start_idx+Dir.SW, start_idx+Dir.NW
    ]
    return hisha + alfil
