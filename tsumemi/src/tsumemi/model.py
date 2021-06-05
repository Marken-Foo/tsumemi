from __future__ import annotations

import os

from typing import TYPE_CHECKING

import tsumemi.src.shogi.kif as kif
import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.timer as timer
import tsumemi.src.tsumemi.move_input_handler as mih
import tsumemi.src.tsumemi.problem_list as plist

from tsumemi.src.shogi.basetypes import TerminationMove
from tsumemi.src.tsumemi.problem_list import Problem, ProblemList

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Optional, Union
    import tsumemi.src.tsumemi.kif_browser_gui as kbg
    from tsumemi.src.shogi.game import Game
    from tsumemi.src.shogi.kif import ParserVisitor, Reader
    from tsumemi.src.tsumemi.problem_list import ProblemStatus
    PathLike = Union[str, os.PathLike]


class Model(evt.IObserver):
    """Main data model of program. Manages reading problems from file
    and maintaining the problem list.
    """
    # This is currently actually a mishmash of Model + controller.
    # Try to refactor the controller bits from MainWindow to here.
    def __init__(self, gui_controller: kbg.RootController) -> None:
        # References to other control or relevant objects
        self.gui_controller = gui_controller
        self.reader: Reader = kif.KifReader()
        # Data
        self.solution: str = ""
        self.active_game: Game = self.reader.game
        
        self.NOTIFY_ACTIONS = {
            mih.MoveEvent: self.add_move,
            timer.TimerSplitEvent: self._on_split
        }
        return
    
    def set_active_problem(self, idx: int = 0) -> bool:
        if self.gui_controller.prob_buffer.is_empty():
            return False
        else:
            if self.gui_controller.prob_buffer.go_to_idx(idx):
                self.read_problem()
            return True
    
    def read_file(self, filename: PathLike,
            reader: Reader, visitor: ParserVisitor
        ) -> None:
        # Get the given reader to read the given file.
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
        # Get the active reader to read the current active problem
        # from file
        filepath = self.gui_controller.prob_buffer.get_curr_filepath()
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
        # Adds all problems in given directory to self.gui_controller.prob_buffer.
        # Does not otherwise alter state of Model.
        if recursive:
            for dirpath, _, filenames in os.walk(directory):
                self.gui_controller.prob_buffer.add_problems([
                    Problem(os.path.join(dirpath, filename))
                    for filename in filenames
                    if filename.endswith(".kif")
                    or filename.endswith(".kifu")
                ], suppress=suppress)
        else:
            with os.scandir(directory) as it:
                self.gui_controller.prob_buffer.add_problems([
                    Problem(os.path.join(directory, entry.name))
                    for entry in it
                    if entry.name.endswith(".kif")
                    or entry.name.endswith(".kifu")
                ], suppress=suppress)
        return
    
    def set_directory(self, directory: PathLike,
            recursive: bool = False
        ) -> bool:
        # Open the given directory and set problem buffer to its
        # contents.
        self.gui_controller.prob_buffer.clear(suppress=True)
        self.add_problems_in_directory(
            directory, recursive=recursive, suppress=True
        )
        self.gui_controller.prob_buffer.sort_by_file()
        return self.set_active_problem()
    
    def get_curr_filepath(self) -> Optional[PathLike]:
        return self.gui_controller.prob_buffer.get_curr_filepath()
    
    def go_to_next_file(self, event: tk.Event = None) -> bool:
        res = False
        if self.gui_controller.prob_buffer.next():
            self.read_problem()
            res = True
        if res:
            self.gui_controller.display_problem()
            self.gui_controller.move_input_handler.set_state("ready")
        return res
    
    def go_to_prev_file(self, event: tk.Event = None) -> bool:
        res = False
        if self.gui_controller.prob_buffer.prev():
            self.read_problem()
            res = True
        if res:
            self.gui_controller.display_problem()
            self.gui_controller.move_input_handler.set_state("ready")
        return res
    
    def go_to_file(self, idx: int = 0, event: tk.Event = None) -> bool:
        res = False
        if self.gui_controller.prob_buffer.go_to_idx(idx):
            self.read_problem()
            res = True
        if res:
            self.gui_controller.display_problem()
            self.gui_controller.move_input_handler.set_state("ready")
        return res
    
    def set_status(self, status: ProblemStatus) -> None:
        self.gui_controller.prob_buffer.set_status(status)
        return
    
    def add_move(self, event: mih.MoveEvent) -> None:
        """Make the move, regardless of whether the move is in the
        game or not.
        """
        move = event.move
        self.active_game.add_move(move)
        self.gui_controller.board.draw()
        return
    
    def verify_move(self, event: mih.MoveEvent) -> None:
        # Used only in speedrun mode
        # given a move sent via input event, check if the move is
        # correct, and if it is, make the move.
        # could possibly be refactored? (Single-responsibility)
        move = event.move
        if self.active_game.is_mainline(move):
            # the move is the mainline, so it is correct
            self.active_game.make_move(move)
            self.gui_controller.board.draw()
            if self.active_game.is_end():
                self.mark_correct_and_pause()
            else:
                response_move = self.active_game.get_mainline_move()
                if type(response_move) == TerminationMove:
                    self.mark_correct_and_pause()
                else:
                    self.active_game.make_move(response_move)
                    self.gui_controller.board.draw()
                    if self.active_game.is_end():
                        self.mark_correct_and_pause()
        else:
            self.mark_wrong_and_pause()
        return
    
    def _on_split(self, event: timer.TimerSplitEvent) -> None:
        if self.gui_controller.main_timer.clock == event.clock and event.time is not None:
            self.gui_controller.prob_buffer.set_time(event.time)
        return
    
    # Speedrun mode methods
    def start_speedrun(self) -> None:
        self.go_to_file(idx=0)
        self.NOTIFY_ACTIONS[mih.MoveEvent] = self.verify_move
        self.gui_controller.set_speedrun_ui()
        self.gui_controller.main_timer.clock.reset()
        self.gui_controller.main_timer.clock.start()
        return
    
    def abort_speedrun(self) -> None:
        self.gui_controller.main_timer.clock.stop()
        self.NOTIFY_ACTIONS[mih.MoveEvent] = self.add_move
        self.gui_controller.remove_speedrun_ui()
        return
    
    def skip(self) -> None:
        self.gui_controller.split_timer()
        self.set_status(plist.ProblemStatus.SKIP)
        if not self.go_to_next_file():
            self.end_of_folder()
        return
    
    def mark_correct_and_pause(self) -> None:
        self.set_status(plist.ProblemStatus.CORRECT)
        self.gui_controller.split_timer()
        self.gui_controller.main_timer.clock.stop()
        self.gui_controller.show_solution()
        self.gui_controller.nav_controls.show_continue()
        return
    
    def mark_wrong_and_pause(self) -> None:
        self.set_status(plist.ProblemStatus.WRONG)
        self.gui_controller.split_timer()
        self.gui_controller.main_timer.clock.stop()
        self.gui_controller.show_solution()
        self.gui_controller.nav_controls.show_continue()
        self.gui_controller.board.draw()
        return
    
    def mark_correct(self) -> None:
        self.set_status(plist.ProblemStatus.CORRECT)
        self.continue_speedrun()
        return
    
    def mark_wrong(self) -> None:
        self.set_status(plist.ProblemStatus.WRONG)
        self.continue_speedrun()
        return
    
    def continue_speedrun(self) -> None:
        # continue speedrun from a pause, answer-checking state.
        if not self.go_to_next_file():
            self.end_of_folder()
            return
        self.gui_controller.nav_controls.show_sol_skip()
        self.gui_controller.main_timer.clock.start()
        return
    
    def end_of_folder(self) -> None:
        self.gui_controller.main_timer.clock.stop()
        self.gui_controller.show_end_of_folder_message()
        self.abort_speedrun()
        return
