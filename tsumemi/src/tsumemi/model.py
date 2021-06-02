from __future__ import annotations

import os

from typing import TYPE_CHECKING

import tsumemi.src.shogi.kif as kif
import tsumemi.src.shogi.rules as rules
import tsumemi.src.tsumemi.timer as timer

from tsumemi.src.shogi.basetypes import Koma, KomaType, Move, Square
from tsumemi.src.tsumemi.problem_list import Problem, ProblemList

if TYPE_CHECKING:
    from typing import List, Optional, Tuple
    from tsumemi.src.shogi.game import Game
    from tsumemi.src.tsumemi.board_canvas import BoardCanvas


class GameAdapter:
    """Links a BoardCanvas (frontend) to a Game (backend).
    Manages the logic flow between the GUI and data model.
    """
    def __init__(self, game: Game, board_canvas: BoardCanvas) -> None:
        self.game = game
        self.position = self.game.position
        self.board_canvas = board_canvas
        self.board_canvas.connect_game_adapter(self)
        self.focused_sq = Square.NONE
        self.focused_ktype = KomaType.NONE
        return
    
    def clear_focus(self) -> None:
        self.focused_sq = Square.NONE
        self.focused_ktype = KomaType.NONE
        self.board_canvas.set_focus(Square.NONE)
        return
    
    def set_focus(self, sq: Square) -> None:
        self.focused_sq = sq
        self.focused_ktype = KomaType.get(self.position.get_koma(sq))
        self.board_canvas.set_focus(sq)
        return
    
    def make_move(self, move: Move) -> None:
        self.game.make_move(move)
        # send message to GUI to update position
        self.board_canvas.draw()
        return
    
    def receive_square(self, event,
            sq: Square, hand_ktype: KomaType = KomaType.NONE
        ) -> None:
        """Receive Square (and/or event) from GUI view, retain the
        information, and decide if it completes a legal move or not.
        """
        # game adapter receives a Square (Event?) from the GUI and
        # decides what to do with it
        koma = self.position.get_koma(sq)
        # debugging prints
        print(event)
        print(koma, sq, hand_ktype, self.position.sq_to_idx(sq))
        print(self.focused_sq, self.focused_ktype, self.position.turn)
        # Selecting the same square deselects it
        if sq == self.focused_sq:
            self.clear_focus()
            return
        # Selecting a hand piece can never complete a move.
        elif sq == Square.HAND:
            self.focused_sq = sq
            self.focused_ktype = hand_ktype
            self.board_canvas.set_focus(sq)
            return
        # If nothing had previously been selected, a move cannot be
        # completed with the current selection.
        elif self.focused_sq == Square.NONE:
            koma = self.position.get_koma(sq)
            if (koma != Koma.NONE) and (koma != Koma.INVALID):
                if koma.side() == self.position.turn:
                    self.set_focus(sq)
            return
        # If a hand piece had previously been selected, consider if a
        # drop move is legal or not.
        elif self.focused_sq == Square.HAND:
            koma = self.position.get_koma(sq)
            if koma == Koma.NONE:
                # create drop moves then check legality
                exists_valid_move, mvlist = self.check_validity(
                    start_sq=self.focused_sq, end_sq=sq,
                    ktype=self.focused_ktype
                )
                if exists_valid_move:
                    # Given the end square and koma type, if a valid
                    # drop exists, it's the only one.
                    if rules.is_legal(mvlist[0], self.position):
                        self.make_move(mvlist[0])
                    self.clear_focus()
                else:
                    self.clear_focus()
                return
            else: # selected a square with a piece
                if koma.side() == self.position.turn:
                    self.set_focus(sq)
                else:
                    self.clear_focus(sq)
                return
        # Else, a board piece had previously been selected, consider
        # if a piece move is legal or not.
        else:
            ktype = KomaType.get(self.position.get_koma(self.focused_sq))
            exists_valid_move, mvlist = self.check_validity(
                start_sq=self.focused_sq, end_sq=sq, ktype=ktype
            )
            if exists_valid_move:
                # For normal shogi, either one move (promo or non)
                # or two (choice between promo or non)
                if len(mvlist) == 1:
                    if rules.is_legal(mvlist[0], self.position):
                        self.make_move(mvlist[0])
                    self.clear_focus()
                elif len(mvlist) == 2:
                    # If the promotion is legal, so is the
                    # nonpromotion, and vice-versa.
                    if rules.is_legal(mvlist[0], self.position):
                        # more info needed, GUI prompts for input
                        self.board_canvas.prompt_promotion(sq, ktype)
                    else:
                        self.clear_focus()
                    return
            else:
                # Not completing a move, update focus accordingly
                koma_new = self.position.get_koma(sq)
                if koma_new == Koma.NONE:
                    self.clear_focus()
                elif koma_new.side() == self.position.turn:
                    self.set_focus(sq)
            return
    
    def execute_promotion_choice(self,
            is_promotion: Optional[bool],
            sq: Square, ktype: KomaType
        ) -> None:
        if is_promotion is None:
            # This means promotion choice is cancelled
            self.clear_focus()
            return
        else:
            # Promotion choice is made, yes or no
            mv = Move(
                start_sq=self.focused_sq, end_sq=sq,
                koma=Koma.make(self.position.turn, ktype),
                captured=self.position.get_koma(sq),
                is_promotion=is_promotion
            )
            self.make_move(mv)
            self.clear_focus()
        return
    
    def check_validity(self,
            start_sq: Square, end_sq: Square,
            ktype: KomaType = KomaType.NONE
        ) -> Tuple[bool, List[Move]]:
        """Decide if there exists a valid move given the start and
        end Squares, and KomaType (needed for hand pieces).
        """
        res_bool = False
        if start_sq == Square.HAND:
            mvlist = rules.generate_drop_moves(
                pos=self.position, side=self.position.turn, ktype=ktype
            )
            mvlist_filtered = [mv for mv in mvlist if (mv.end_sq == end_sq)]
            if len(mvlist_filtered) == 1:
                res_bool = True
            return res_bool, mvlist_filtered
        # Now start_sq should be a valid Square on the board
        koma = self.position.get_koma(start_sq)
        if koma.side() == self.position.turn:
            ktype = KomaType.get(koma)
            mvlist = rules.generate_valid_moves(
                pos=self.position, side=self.position.turn, ktype=ktype
            )
            mvlist_filtered = [
                mv for mv in mvlist
                if (mv.start_sq == start_sq) and (mv.end_sq == end_sq)
            ]
            if (len(mvlist_filtered) == 1) or (len(mvlist_filtered) == 2):
                res_bool = True
            return res_bool, mvlist_filtered
        return False, []


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
