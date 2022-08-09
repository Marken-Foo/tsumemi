from __future__ import annotations

import logging

from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.game_controller as gamecon
import tsumemi.src.tsumemi.problem_list as plist

if TYPE_CHECKING:
    import tkinter as tk
    from typing import Dict
    from tsumemi.src.tsumemi.kif_browser_gui import RootController

logger = logging.getLogger(__name__)


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
        self._state_change_callback(new_state)
        return
    
    def _state_change_callback(self, state: SpeedrunState) -> None:
        if isinstance(state, SpeedrunQuestionState):
            constructor = self.make_nav_pane_question
            self.target.update_nav_control_pane(constructor)
        elif isinstance(state, SpeedrunAnswerState):
            constructor = self.make_nav_pane_answer
            self.target.update_nav_control_pane(constructor)
        elif isinstance(state, SpeedrunSolutionState):
            constructor = self.make_nav_pane_solution
            self.target.update_nav_control_pane(constructor)
        return
    
    def start_speedrun(self) -> None:
        self.target.go_to_file(idx=0)
        self.target.main_game.set_speedrun_mode()
        self.target.mainframe.main_timer_view.allow_only_pause()
        self.target.main_timer.reset()
        self.start_timer()
        self.go_to_state("question")
        return
    
    def abort_speedrun(self) -> None:
        self.stop_timer()
        self.target.mainframe.main_timer_view.allow_all()
        self.target.main_game.set_free_mode()
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
        self.target.mainframe.show_solution()
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
    
    def disable_solving(self) -> None:
        self.target.mainframe.disable_move_input()
        return
    
    def enable_solving(self) -> None:
        self.target.mainframe.enable_move_input()
        return
    
    def make_nav_pane_question(self, parent: tk.Widget) -> ttk.Frame:
        nav = ttk.Frame(parent) #NavControlPane
        question_state = self._speedrun_states["question"]
        if not isinstance(question_state, SpeedrunQuestionState):
            logger.warning("speedrun question state missing")
            return nav
        btn_show_solution = ttk.Button(nav,
            text="Show solution",
            command=question_state.show_answer
        )
        btn_show_solution.grid(
            row=0, column=0, sticky="E",
            padx=5, pady=5
        )
        btn_skip = ttk.Button(nav,
            text="Skip",
            command=question_state.skip
        )
        btn_skip.grid(
            row=0, column=1, sticky="W",
            padx=5, pady=5
        )
        return nav
    
    def make_nav_pane_answer(self, parent: tk.Widget) -> ttk.Frame:
        nav = ttk.Frame(parent) #NavControlPane
        answer_state = self._speedrun_states["answer"]
        if not isinstance(answer_state, SpeedrunAnswerState):
            logger.warning("speedrun answer state missing")
            return nav
        btn_correct = ttk.Button(nav,
            text="Correct",
            command=answer_state.mark_correct_and_continue
        )
        btn_correct.grid(
            row=0, column=0, sticky="E",
            padx=5, pady=5
        )
        btn_wrong = ttk.Button(nav,
            text="Wrong",
            command=answer_state.mark_wrong_and_continue
        )
        btn_wrong.grid(
            row=0, column=1, sticky="W",
            padx=5, pady=5
        )
        return nav
    
    def make_nav_pane_solution(self, parent: tk.Widget) -> ttk.Frame:
        nav = ttk.Frame(parent) #NavControlPane
        solution_state = self._speedrun_states["solution"]
        if not isinstance(solution_state, SpeedrunSolutionState):
            logger.warning("speedrun solution state missing")
            return nav
        btn_continue = ttk.Button(nav,
            text="Next",
            command=solution_state.next_question
        )
        btn_continue.grid(
            row=0, column=0,
            padx=5, pady=5
        )
        return nav


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
        self.set_callbacks({
            gamecon.GameEndEvent: self._mark_correct,
            gamecon.WrongMoveEvent: self._mark_wrong,
        })
        return
    
    def on_entry(self) -> None:
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
        return
    
    def next_question(self) -> None:
        if self.controller.go_next_question():
            self.controller.go_to_state("question")
        return


class SpeedrunOffState(SpeedrunState):
    # Default state
    pass