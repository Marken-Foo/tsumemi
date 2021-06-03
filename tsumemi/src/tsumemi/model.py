from __future__ import annotations

import os

from typing import TYPE_CHECKING

import tsumemi.src.shogi.kif as kif
import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.timer as timer
import tsumemi.src.tsumemi.move_input_handler as mih

from tsumemi.src.shogi.basetypes import TerminationMove
from tsumemi.src.tsumemi.problem_list import Problem, ProblemList

if TYPE_CHECKING:
    from typing import Optional, Union
    import tsumemi.src.tsumemi.kif_browser_gui as kbg
    from tsumemi.src.shogi.game import Game
    from tsumemi.src.shogi.kif import ParserVisitor, Reader
    from tsumemi.src.tsumemi.problem_list import ProblemStatus
    PathLike = Union[str, os.PathLike]


# class AppMode:
    # """Base class for the states the application can be in.
    # Currently free browsing mode or speedrun mode.
    # """
    # pass

# class FreeMode(AppMode):


class Model(evt.IObserver):
    """Main data model of program. Manages reading problems from file
    and maintaining the problem list.
    """
    def __init__(self, gui_controller: kbg.MainWindow) -> None:
        # References to other control or relevant objects
        self.gui_controller = gui_controller
        self.reader: Reader = kif.KifReader()
        # Data
        self.prob_buffer: ProblemList = ProblemList()
        self.directory: PathLike = "" # not currently used meaningfully
        self.solution: str = ""
        self.active_game: Game = self.reader.game
        self.clock: timer.Timer = timer.Timer()
        self.clock.add_observer(self)
        
        self.NOTIFY_ACTIONS = {
            mih.MoveEvent: self.verify_move,
            timer.TimerSplitEvent: self._on_split
        }
        return
    
    def set_active_problem(self, idx: int = 0) -> bool:
        if self.prob_buffer.is_empty():
            return False
        else:
            if self.prob_buffer.go_to_idx(idx):
                self.read_problem()
            return True
    
    def read_file(self, filename: PathLike,
            reader: Reader, visitor: ParserVisitor
        ) -> None:
        encodings = ["cp932", "utf-8"]
        for enc in encodings:
            try:
                with open(filename, "r", encoding=enc) as kif:
                    reader.read(kif, visitor)
            except UnicodeDecodeError:
                pass
            else:
                break
        return
    
    def read_problem(self) -> None:
        # loads position and moves as a Game in the reader, returns None
        filepath = self.prob_buffer.get_curr_filepath()
        if filepath is None:
            return # error out?
        self.read_file(filepath, reader=self.reader,
            visitor=kif.GameBuilderPVis()
        )
        self.solution = "　".join(self.reader.game.to_notation_ja_kif())
        self.active_game = self.reader.game
        self.active_game.start()
        return
    
    def add_problems_in_directory(self, directory: PathLike,
            recursive: bool = False, suppress: bool = False
        ) -> None:
        # Adds all problems in given directory to self.prob_buffer.
        # Does not otherwise alter state of Model.
        if recursive:
            for dirpath, _, filenames in os.walk(directory):
                self.prob_buffer.add_problems([
                    Problem(os.path.join(dirpath, filename))
                    for filename in filenames
                    if filename.endswith(".kif")
                    or filename.endswith(".kifu")
                ], suppress=suppress)
        else:
            with os.scandir(directory) as it:
                self.prob_buffer.add_problems([
                    Problem(os.path.join(directory, entry.name))
                    for entry in it
                    if entry.name.endswith(".kif")
                    or entry.name.endswith(".kifu")
                ], suppress=suppress)
        return
    
    def set_directory(self, directory: PathLike,
            recursive: bool = False
        ) -> bool:
        self.directory = directory
        self.prob_buffer.clear(suppress=True)
        self.add_problems_in_directory(
            directory, recursive=recursive, suppress=True
        )
        self.prob_buffer.sort_by_file()
        return self.set_active_problem()
    
    def get_curr_filepath(self) -> Optional[PathLike]:
        return self.prob_buffer.get_curr_filepath()
    
    def open_next_file(self) -> bool:
        if self.prob_buffer.next():
            self.read_problem()
            return True
        else:
            return False
    
    def open_prev_file(self) -> bool:
        if self.prob_buffer.prev():
            self.read_problem()
            return True
        else:
            return False
    
    def open_file(self, idx: int) -> bool:
        if self.prob_buffer.go_to_idx(idx):
            self.read_problem()
            return True
        else:
            return False
    
    def set_status(self, status: ProblemStatus) -> None:
        self.prob_buffer.set_status(status)
        return
    
    def verify_move(self, event: mih.MoveEvent) -> None:
        move = event.move
        if self.active_game.is_mainline(move):
            # the move is the mainline, so it is correct
            self.active_game.make_move(move)
            self.gui_controller.board.draw()
            if self.active_game.is_end():
                pass
            else:
                response_move = self.active_game.get_mainline_move()
                if type(response_move) == TerminationMove:
                    pass
                else:
                    self.active_game.make_move(response_move)
                    self.gui_controller.board.draw()
        else:
            # self.active_game.make_move(move)
            self.gui_controller.board.draw()
        return
    
    def _on_split(self, event: timer.TimerSplitEvent) -> None:
        if self.clock == event.clock and event.time is not None:
            self.prob_buffer.set_time(event.time)
        return
    
    # Timer clock controls
    def start_timer(self) -> None:
        self.clock.start()
        return
    
    def stop_timer(self) -> None:
        self.clock.stop()
        return
    
    def toggle_timer(self) -> None:
        self.clock.toggle()
        return
    
    def reset_timer(self) -> None:
        self.clock.reset()
        return
    
    def split_timer(self) -> None:
        time = self.clock.split()
        if time is not None:
            self.prob_buffer.set_time(time)
        return
