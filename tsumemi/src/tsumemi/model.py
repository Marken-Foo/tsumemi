from __future__ import annotations

import os

import tsumemi.src.shogi.kif as kif
import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.timer as timer

from tsumemi.src.tsumemi.problem_list import Problem, ProblemList


class Model(evt.IObserver):
    """Main data model of program. Manages reading problems from file
    and maintaining the problem list.
    """
    def __init__(self):
        self.prob_buffer = ProblemList()
        self.directory = None # not currently used meaningfully
        self.solution = ""
        self.reader = kif.KifReader()
        self.active_game = self.reader.game
        self.clock = timer.Timer()
        self.game_adapter = None
        
        self.NOTIFY_ACTIONS: Dict[Type[Event], Callable[..., Any]] = {
            timer.TimerSplitEvent: self._on_split
        }
        self.clock.add_observer(self)
        return
    
    def set_active_problem(self, idx=0):
        if self.prob_buffer.is_empty():
            return False
        else:
            if self.prob_buffer.go_to_idx(idx):
                self.read_problem()
            return True
    
    def read_file(self, filename, reader, visitor):
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
    
    def read_problem(self):
        # loads position and moves as a Game in the reader, returns None
        self.read_file(
            self.prob_buffer.get_curr_filepath(),
            reader=self.reader,
            visitor=kif.GameBuilderPVis()
        )
        self.solution = "　".join(self.reader.game.to_notation_ja_kif())
        self.reader.game.start()
        return
    
    def add_problems_in_directory(self,
            directory, recursive=False, suppress=False
        ):
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
    
    def set_directory(self, directory, recursive=False):
        self.directory = directory
        self.prob_buffer.clear(suppress=True)
        self.add_problems_in_directory(
            directory, recursive=recursive, suppress=True
        )
        self.prob_buffer.sort_by_file()
        return self.set_active_problem()
    
    def get_curr_filepath(self):
        return self.prob_buffer.get_curr_filepath()
    
    def open_next_file(self):
        if self.prob_buffer.next():
            self.read_problem()
            return True
        else:
            return False
    
    def open_prev_file(self):
        if self.prob_buffer.prev():
            self.read_problem()
            return True
        else:
            return False
    
    def open_file(self, idx):
        if self.prob_buffer.go_to_idx(idx):
            self.read_problem()
            return True
        else:
            return False
    
    def set_status(self, status):
        self.prob_buffer.set_status(status)
        return
    
    def _on_split(self, event):
        if self.clock == event.clock and event.time is not None:
            self.prob_buffer.set_time(event.time)
        return
    
    # Timer clock controls
    def start_timer(self):
        self.clock.start()
        return
    
    def stop_timer(self):
        self.clock.stop()
        return
    
    def toggle_timer(self):
        self.clock.toggle()
        return
    
    def reset_timer(self):
        self.clock.reset()
        return
    
    def split_timer(self):
        time = self.clock.split()
        if time is not None:
            self.prob_buffer.set_time(time)
        return
