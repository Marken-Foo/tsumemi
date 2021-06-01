from __future__ import annotations

import os

import tsumemi.src.shogi.kif as kif
import tsumemi.src.shogi.rules as rules
import tsumemi.src.tsumemi.timer as timer

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Square
from tsumemi.src.shogi.game import Game
from tsumemi.src.tsumemi.board_canvas import BoardCanvas
from tsumemi.src.tsumemi.problem_list import Problem, ProblemList


class GameAdapter:
    # Manages logic flow between GUI and model.
    def __init__(self, game: Game, board_canvas: BoardCanvas):
        self.game = game
        self.position = self.game.position
        self.board_canvas = board_canvas
        self.focused_sq = Square.NONE
        self.focused_ktype = KomaType.NONE
        return
    
    def clear_focus(self) -> None:
        self.focused_sq = Square.NONE
        self.focused_ktype = KomaType.NONE
        return
    
    def receive_square(self, event,
            sq: Square, hand_ktype: KomaType = KomaType.NONE
        ) -> None:
        # game adapter receives a Square (Event?) from the GUI and
        # decides what to do with it
        koma = self.position.get_koma(sq)
        print(koma, sq, hand_ktype, self.position.sq_to_idx(sq))
        print(self.focused_sq, self.focused_ktype, self.position.turn)
        if sq == Square.HAND:
            # Selecting a hand piece can never complete a move.
            self.focused_sq = sq
            self.focused_ktype = hand_ktype
            # send message to change focus
            return
        elif self.focused_sq == Square.NONE:
            # If nothing had previously been selected, a move cannot
            # be completed with the current selection.
            koma = self.position.get_koma(sq)
            if (koma != Koma.NONE) and (koma != Koma.INVALID):
                self.focused_sq = sq
                self.focused_ktype = KomaType.get(koma)
                # send message to change focus
                return
            else:
                return
        elif self.focused_sq == Square.HAND:
            koma = self.position.get_koma(sq)
            if koma == Koma.NONE:
                # create drop moves then check legality
                if self.validate_legality(
                        start_sq=self.focused_sq, end_sq=sq,
                        ktype=self.focused_ktype
                    ):
                    mv = Move(
                        start_sq=self.focused_sq, end_sq=sq,
                        koma=Koma.make(self.position.turn, self.focused_ktype)
                    )
                    self.game.make_move(mv)
                    self.board_canvas.draw()
                    # if legal make move, else remove focus
                return
            else:
                self.focused_sq = sq
                if koma.side() == self.position.turn:
                    self.focused_ktype = KomaType.get(koma)
                # change focus to newly selected hand piece
                return
        else:
            # this is if focused square contains valid koma already
            # TODO: this is only valid moves!
            ktype = KomaType.get(self.position.get_koma(self.focused_sq))
            if self.validate_legality(
                    start_sq=self.focused_sq, end_sq=sq, ktype=ktype
                ):
                # TODO: promotion prompts
                mv = Move(
                    start_sq=self.focused_sq, end_sq=sq,
                    koma=Koma.make(self.position.turn, ktype),
                    captured=self.position.get_koma(sq)
                )
                self.make_move(mv)
                self.clear_focus()
            else:
                # Not completing a move, update focus accordingly
                if self.position.get_koma(sq) == Koma.NONE:
                    self.clear_focus()
                else:
                    self.focused_sq = sq
                    self.focused_ktype = KomaType.get(self.position.get_koma(sq))
            return
    
    def make_move(self, move: Move) -> None:
        self.game.make_move(move)
        # send message to GUI to update position
        self.board_canvas.draw()
        return
    
    def validate_legality(self,
            start_sq: Square, end_sq: Square,
            ktype: KomaType = KomaType.NONE
        ) -> bool:
        # This ONLY validates legality, making move is up to caller
        # check if drop
        if start_sq == Square.HAND:
            # TODO: this is VALID, not LEGAL yet
            mvlist = rules.generate_drop_moves(
                pos=self.position, side=self.position.turn, ktype=ktype
            )
            mvlist_filtered = [mv for mv in mvlist if (mv.end_sq == end_sq)]
            if len(mvlist_filtered) == 1:
                return True
            elif len(mvlist_filtered) == 0:
                # there is no legal drop move
                return False
            else:
                # Something is very wrong
                return False
        koma = self.position.get_koma(start_sq)
        if koma.side() != self.position.turn:
            return False
        else:
            # TODO: generate (LEGAL NOT VALID) moves of said piece type
            ktype = KomaType.get(koma)
            mvlist = rules.generate_valid_moves(
                pos=self.position, side=self.position.turn, ktype=ktype
            )
            mvlist_filtered = [
                mv for mv in mvlist
                if (mv.start_sq == start_sq) and (mv.end_sq == end_sq)
            ]
            if len(mvlist_filtered) == 1:
                return True
            elif len(mvlist_filtered) == 2:
                # needs promotion
                # invoke other function, or send message to GUI to prompt for promotion?
                return True
            elif len(mvlist_filtered) == 0:
                # no such move
                return False
            else:
                # ?????? how did this happen
                return False
        


class Model:
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
