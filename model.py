import os
import re

from enum import Enum

from event import Emitter, ProbListEvent, ProbStatusEvent, ProbTimeEvent
from kif_parser import KifReader


class ProblemStatus(Enum):
    NONE = 0; CORRECT = 1; WRONG = 2; SKIP = 3


class Problem:
    '''Data class representing one tsume problem.'''
    def __init__(self, filepath):
        self.filepath = filepath
        self.time = None
        self.status = ProblemStatus.NONE
        return
    
    def get_filepath(self):
        return self.filepath
    
    def __eq__(self, obj):
        # For future use
        return isinstance(obj, Problem) and self.filepath == obj.filepath


class ProblemList(Emitter):
    @staticmethod
    def natural_sort_key(str, _nsre=re.compile(r'(\d+)')):
        return [int(c) if c.isdigit() else c.lower() for c in _nsre.split(str)]
    
    def __init__(self):
        self.problems = []
        self.curr_prob = None
        self.curr_prob_idx = None
        self.observers = []
        return
    
    def clear(self, suppress=False):
        self.problems = []
        self.curr_prob = None
        self.curr_prob_idx = None
        if not suppress:
            self._notify_observers(ProbListEvent(self.problems))
        return
    
    def add_problems(self, new_problems, suppress=False):
        self.problems.extend(new_problems)
        if not suppress:
            self._notify_observers(ProbListEvent(self.problems))
        return
    
    def sort(self, suppress=False, *args, **kwargs):
        res = self.problems.sort(*args, **kwargs)
        if not suppress:
            self._notify_observers(ProbListEvent(self.problems))
        return res
    
    def get_curr_filepath(self):
        if self.curr_prob is None:
            return None
        else:
            return self.curr_prob.get_filepath()
    
    def set_status(self, status):
        if self.curr_prob is not None:
            self.curr_prob.status = status
            self._notify_observers(ProbStatusEvent(self.curr_prob_idx, status))
        return
    
    def set_time(self, time):
        if self.curr_prob is not None:
            self.curr_prob.time = time
            self._notify_observers(ProbTimeEvent(self.curr_prob_idx, time))
        return
    
    def next(self):
        if self.curr_prob_idx+1 >= len(self.problems):
            return False
        self.curr_prob = self.problems[self.curr_prob_idx + 1]
        self.curr_prob_idx += 1
        return True
    
    def prev(self):
        if self.curr_prob_idx-1 < 0:
            return False
        self.curr_prob = self.problems[self.curr_prob_idx - 1]
        self.curr_prob_idx -= 1
        return True
    
    def go_to_idx(self, idx):
        if idx >= len(self.problems) or idx < 0:
            return False
        self.curr_prob = self.problems[idx]
        self.curr_prob_idx = idx
        return True


class Model():
    # Following MVC principles, this is the data model of the program.
    def __init__(self):
        self.prob_buffer = ProblemList()
        self.directory = None # not currently used meaningfully
        self.solution = ""
        self.reader = KifReader()
    
    def read_problem(self):
        # Read current problem into reader.
        # Try any likely encodings for the KIF files
        encodings = ["cp932", "utf-8"]
        for e in encodings:
            try:
                with open(self.prob_buffer.get_curr_filepath(),\
                          "r", encoding=e) as kif:
                    self.reader.parse_kif(kif)
                    self.solution = "　".join(self.reader.moves)
            except UnicodeDecodeError:
                pass
            else:
                break
        return self.reader
    
    def set_directory(self, directory):
        self.directory = directory
        self.prob_buffer.clear(suppress=True)
        with os.scandir(directory) as it:
            self.prob_buffer.add_problems([
                Problem(os.path.join(directory, entry.name))
                for entry in it
                if entry.name.endswith(".kif") or entry.name.endswith(".kifu")
            ], suppress=True)
        self.prob_buffer.sort(key=lambda p:\
                                  ProblemList.natural_sort_key(p.filepath))
        self.prob_buffer.go_to_idx(0)
        self.read_problem()
        return
    
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
    
    def set_time(self, status):
        self.prob_buffer.set_time(status)
        return
