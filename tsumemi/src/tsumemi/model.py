import os

from tsumemi.src.tsumemi.kif_parser import KifReader
from tsumemi.src.tsumemi.problem_list import Problem, ProblemList


class Model():
    """Main data model of program, following MVC principles. Manages
    reading problems from file and maintaining the problem list.
    """
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
