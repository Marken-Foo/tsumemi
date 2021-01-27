import os
import re

from enum import Enum
from random import shuffle

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
        # Used in tests, will be useful in future features
        return isinstance(obj, Problem) and self.filepath == obj.filepath


class CmdSortProbList:
    def __init__(self, prob_list):
        self.prob_list = prob_list
        return
    
    def by_file(self):
        return self.prob_list.sort_by_file()
    
    def by_time(self):
        return self.prob_list.sort_by_time()
    
    def by_status(self):
        return self.prob_list.sort_by_status()
    
    def randomise(self):
        return self.prob_list.randomise()


class ProblemList(Emitter):
    @staticmethod
    def natural_sort_key(str, _nsre=re.compile(r'(\d+)')):
        return [int(c) if c.isdigit() else c.lower() for c in _nsre.split(str)]
    
    @staticmethod
    def _file_key(prob):
        return ProblemList.natural_sort_key(prob.filepath)
    
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
    
    def is_empty(self):
        return False if self.problems else True
    
    def add_problems(self, new_problems, suppress=False):
        self.problems.extend(new_problems)
        if not suppress:
            self._notify_observers(ProbListEvent(self.problems))
        return
    
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
        return (False if self.curr_prob_idx is None
            else self.go_to_idx(self.curr_prob_idx + 1))
    
    def prev(self):
        return (False if self.curr_prob_idx is None
            else self.go_to_idx(self.curr_prob_idx - 1))
    
    def go_to_idx(self, idx):
        if idx is None or idx >= len(self.problems) or idx < 0:
            return False
        self.curr_prob = self.problems[idx]
        self.curr_prob_idx = idx
        return True
    
    def set_active_problem(self, prob):
        if prob in self.problems:
            idx = self.problems.index(prob)
            self.curr_prob_idx = idx
            self.curr_prob = self.problems[self.curr_prob_idx]
            return True
        else:
            return False
    
    def sort(self, key, suppress=False):
        # Sorts problem list in-place, keeps focus on same problem
        prob = self.curr_prob
        res = self.problems.sort(key=key)
        self.set_active_problem(prob)
        if not suppress:
            self._notify_observers(ProbListEvent(self.problems))
        return res
    
    def sort_by_file(self):
        return self.sort(key=ProblemList._file_key)
    
    def sort_by_time(self):
        return self.sort(key=lambda p: p.time)
    
    def sort_by_status(self):
        return self.sort(key=lambda p: p.status.name)
    
    def randomise(self):
        # Randomise problem list, but keep focus on the same problem
        z = list(zip(range(len(self.problems)), self.problems))
        shuffle(z)
        idxs, probs = zip(*z)
        self.problems = list(probs)
        self.curr_prob_idx = idxs.index(self.curr_prob_idx)
        curr_prob = self.problems[self.curr_prob_idx]
        self._notify_observers(ProbListEvent(self.problems))
        return


class Model():
    # Following MVC principles, this is the data model of the program.
    def __init__(self):
        self.prob_buffer = ProblemList()
        self.directory = None # not currently used meaningfully
        self.solution = ""
        self.reader = KifReader()
    
    def set_active_problem(self, idx=0):
        if self.prob_buffer.is_empty():
            return False
        else:
            if self.prob_buffer.go_to_idx(idx):
                self.read_problem()
            return True
    
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
    
    def add_problems_in_directory(self, directory, recursive=False, suppress=False):
        # Adds all problems in given directory to self.prob_buffer.
        # Does not otherwise alter state of Model.
        if recursive:
            for dirpath, _, filenames in os.walk(directory):
                self.prob_buffer.add_problems([
                    Problem(os.path.join(dirpath, filename))
                    for filename in filenames
                    if filename.endswith(".kif") or filename.endswith(".kifu")
                ], suppress=suppress)
        else:
            with os.scandir(directory) as it:
                self.prob_buffer.add_problems([
                    Problem(os.path.join(directory, entry.name))
                    for entry in it
                    if entry.name.endswith(".kif") or entry.name.endswith(".kifu")
                ], suppress=suppress)
        return
    
    def set_directory(self, directory, recursive=False):
        self.directory = directory
        self.prob_buffer.clear(suppress=True)
        self.add_problems_in_directory(directory, recursive=recursive, suppress=True)
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
    
    def set_time(self, status):
        self.prob_buffer.set_time(status)
        return
