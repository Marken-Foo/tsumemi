from __future__ import annotations

from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt

from tsumemi.src.shogi.game import Game

if TYPE_CHECKING:
    from typing import Iterator, List
    from tsumemi.src.shogi.basetypes import Move
    from tsumemi.src.shogi.gametree import MoveNode
    from tsumemi.src.shogi.position import Position


class GameUpdateEvent(evt.Event):
    def __init__(self, game: GameModel) -> None:
        evt.Event.__init__(self)
        self.game = game
        return


class GameModel(evt.Emitter):
    """Wrapper for a Game.
    """
    def __init__(self) -> None:
        evt.Emitter.__init__(self)
        self.game = Game()
        return

    def copy_from(self, game: Game) -> None:
        self.game.copy_from(game)
        self._notify_observers(GameUpdateEvent(self))
        return

    def go_to_start(self) -> None:
        self.game.go_to_start()
        self._notify_observers(GameUpdateEvent(self))
        return

    def go_to_end(self) -> None:
        self.game.go_to_end()
        self._notify_observers(GameUpdateEvent(self))
        return

    def go_next_move(self) -> None:
        self.game.go_next_move()
        self._notify_observers(GameUpdateEvent(self))
        return

    def go_prev_move(self) -> None:
        self.game.go_prev_move()
        self._notify_observers(GameUpdateEvent(self))
        return

    def go_to_id(self, id_: int) -> None:
        self.game.go_to_id(id_)
        self._notify_observers(GameUpdateEvent(self))
        return

    def add_move(self, move: Move) -> None:
        self.game.add_move(move)
        self._notify_observers(GameUpdateEvent(self))
        return

    def make_move(self, move: Move) -> None:
        self.game.make_move(move)
        self._notify_observers(GameUpdateEvent(self))
        return

    def get_initial_sfen(self) -> str:
        return self.game.movetree.start_pos

    def get_current_sfen(self) -> str:
        return self.game.get_current_sfen()

    def get_position(self) -> Position:
        return self.game.position

    def get_current_mainline(self) -> Iterator[MoveNode]:
        """Returns a generator for the mainline of the current node.
        The mainline consists of every node from the root node to the
        current node, and all the first child nodes after it.
        """
        return (self.game.curr_node
            .get_last_node()
            .get_path_from_root()
        )

    def get_current_variation_nodes(self) -> List[MoveNode]:
        """Returns a list of child nodes of the current node.
        """
        return self.game.curr_node.variations
