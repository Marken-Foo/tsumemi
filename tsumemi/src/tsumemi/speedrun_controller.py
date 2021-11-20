from __future__ import annotations

from tkinter import messagebox
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.game_controller as gamecon
import tsumemi.src.tsumemi.problem_list as plist

if TYPE_CHECKING:
    from typing import Dict
    from tsumemi.src.tsumemi.kif_browser_gui import RootController


class SpeedrunController:
    def __init__(self, root_controller: RootController) -> None:
        self.target = root_controller
        self._speedrun_states: Dict[str, SpeedrunState] = {
            "answer": SpeedrunAnswerState(controller=self),
            "off": SpeedrunOffState(controller=self),
            "pause": SpeedrunPauseState(controller=self),
            "question": SpeedrunQuestionState(controller=self),
            "solution": SpeedrunSolutionState(controller=self),
        }
        self.current_speedrun_state = self._speedrun_states["off"]
        return
    
    def go_to_state(self, state: str) -> None:
        old_state = self.current_speedrun_state
        new_state = self._speedrun_states[state]
        old_state.on_exit()
        new_state.on_entry()
        self.current_speedrun_state = new_state
        return
    
    def start_speedrun(self) -> None:
        self.target.go_to_file(idx=0)
        self.target.main_game.set_speedrun_mode()
        self.target.set_speedrun_ui()
        self.target.main_timer_view.allow_only_pause()
        self.target.main_timer.reset()
        self.start_timer()
        self.target.btn_speedrun.config(state="disabled")
        self.target.btn_abort_speedrun.config(state="normal")
        self.go_to_state("question")
        return
    
    def abort_speedrun(self) -> None:
        self.stop_timer()
        self.target.main_timer_view.allow_all()
        self.target.main_game.set_free_mode()
        self.target.remove_speedrun_ui()
        self.target.btn_speedrun.config(state="normal")
        self.target.btn_abort_speedrun.config(state="disabled")
        self.go_to_state("off")
        return
    
    def go_next_question(self) -> bool:
        has_next: bool = self.target.go_next_file()
        if not has_next:
            # end of folder reached
            self.stop_timer()
            messagebox.showinfo(
                title="End of folder",
                message="You have reached the end of the speedrun."
            )
            self.abort_speedrun()
        return has_next
    
    def show_solution(self) -> None:
        self.target.lbl_solution.show_solution()
        return
    
    def start_timer(self) -> None:
        self.target.main_timer.start()
        return
    
    def stop_timer(self) -> None:
        self.target.main_timer.stop()
        return
    
    def split_timer(self) -> None:
        self.target.main_timer.split()
        return
    
    def mark_correct(self) -> None:
        self.target.main_problem_list.set_status(plist.ProblemStatus.CORRECT)
        return
    
    def mark_wrong(self) -> None:
        self.target.main_problem_list.set_status(plist.ProblemStatus.WRONG)
        return
    
    def mark_skip(self) -> None:
        self.target.main_problem_list.set_status(plist.ProblemStatus.SKIP)
        return
    
    def show_continue(self) -> None:
        self.target.nav_controls.show_continue()
        return
    
    def show_correct_wrong(self) -> None:
        self.target.nav_controls.show_correct_wrong()
        return
    
    def show_sol_skip(self) -> None:
        self.target.nav_controls.show_sol_skip()
        return
    
    def disable_solving(self) -> None:
        move_input_handler = self.target.board.move_input_handler
        if move_input_handler is not None:
            move_input_handler.disable()
        return
    
    def enable_solving(self) -> None:
        move_input_handler = self.target.board.move_input_handler
        if move_input_handler is not None:
            move_input_handler.enable()
        return


class SpeedrunState(evt.IObserver):
    def __init__(self, controller: SpeedrunController) -> None:
        self.controller = controller
        return
    
    def on_entry(self) -> None:
        return
    
    def on_exit(self) -> None:
        return


class SpeedrunQuestionState(SpeedrunState):
    def __init__(self, controller: SpeedrunController) -> None:
        SpeedrunState.__init__(self, controller)
        self.NOTIFY_ACTIONS = {
            gamecon.GameEndEvent: self._mark_correct,
            gamecon.WrongMoveEvent: self._mark_wrong,
        }
        return
    
    def on_entry(self) -> None:
        self.controller.show_sol_skip()
        self.controller.start_timer()
        return
    
    def skip(self) -> None:
        self.controller.split_timer()
        self.controller.mark_skip()
        if self.controller.go_next_question():
            self.controller.go_to_state("question")
        return
    
    def _mark_correct(self, event: evt.Event) -> None:
        self.controller.mark_correct()
        self.controller.go_to_state("solution")
        return
    
    def _mark_wrong(self, event: evt.Event) -> None:
        self.controller.mark_wrong()
        self.controller.go_to_state("solution")
        return
    
    def show_answer(self) -> None:
        self.controller.go_to_state("answer")
        return
    
    def pause(self):
        self.controller.go_to_state("pause")
        return


class SpeedrunPauseState(SpeedrunState):
    # Should it disable showing solution?
    def on_entry(self) -> None:
        self.controller.stop_timer()
        self.controller.disable_solving()
        return
    
    def on_exit(self) -> None:
        self.controller.enable_solving()
        return
    
    def unpause(self) -> None:
        self.controller.go_to_state("question")
        return


class SpeedrunAnswerState(SpeedrunState):
    def on_entry(self) -> None:
        self.controller.split_timer()
        self.controller.stop_timer()
        self.controller.show_solution()
        self.controller.show_correct_wrong()
        return
    
    def mark_correct_and_continue(self) -> None:
        self.controller.mark_correct()
        if self.controller.go_next_question():
            self.controller.go_to_state("question")
        return
    
    def mark_wrong_and_continue(self) -> None:
        self.controller.mark_wrong()
        if self.controller.go_next_question():
            self.controller.go_to_state("question")
        return


class SpeedrunSolutionState(SpeedrunState):
    def on_entry(self) -> None:
        self.controller.split_timer()
        self.controller.stop_timer()
        self.controller.show_solution()
        self.controller.show_continue()
        return
    
    def next_question(self) -> None:
        if self.controller.go_next_question():
            self.controller.go_to_state("question")
        return


class SpeedrunOffState(SpeedrunState):
    # Default state
    pass