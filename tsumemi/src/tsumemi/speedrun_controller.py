from __future__ import annotations

import logging

from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.problem as pb
from tsumemi.src.tsumemi.speedrun_states import (
    ReviewAnswer,
    NotInSpeedrun,
    Paused,
    Solving,
    SolutionShown,
    SpeedrunState,
)

if TYPE_CHECKING:
    import tkinter as tk
    from tsumemi.src.tsumemi.kif_browser_gui import RootController

logger = logging.getLogger(__name__)


class SpeedrunController:
    def __init__(self, root_controller: RootController) -> None:
        self.target = root_controller
        self._speedrun_states: dict[str, SpeedrunState] = {
            "answer": ReviewAnswer(controller=self),
            "off": NotInSpeedrun(controller=self),
            "pause": Paused(controller=self),
            "question": Solving(controller=self),
            "solution": SolutionShown(controller=self),
        }
        self.current_speedrun_state = self._speedrun_states["off"]

    def go_to_state(self, state: str) -> None:
        old_state = self.current_speedrun_state
        new_state = self._speedrun_states[state]
        old_state.on_exit()
        new_state.on_entry()
        self.current_speedrun_state = new_state
        self._state_change_callback(new_state)

    def _state_change_callback(self, state: SpeedrunState) -> None:
        if isinstance(state, Solving):
            constructor = self.make_nav_pane_question
            self.target.update_nav_control_pane(constructor)
        elif isinstance(state, ReviewAnswer):
            constructor = self.make_nav_pane_answer
            self.target.update_nav_control_pane(constructor)
        elif isinstance(state, SolutionShown):
            constructor = self.make_nav_pane_solution
            self.target.update_nav_control_pane(constructor)

    def start_speedrun(self) -> None:
        self.target.go_to_file(idx=0)
        self.target.main_game.set_speedrun_mode()
        self.target.main_viewcon.disable_problem_list_input()
        self.target.main_viewcon.allow_only_pause_timer()
        self.target.main_timer.reset()
        self.start_timer()
        self.go_to_state("question")

    def abort_speedrun(self) -> None:
        self.stop_timer()
        self.target.main_viewcon.allow_all_timer()
        self.target.main_game.set_free_mode()
        self.enable_move_navigation()
        self.target.main_viewcon.enable_problem_list_input()
        self.go_to_state("off")

    def go_next_question(self) -> bool:
        has_next: bool = self.target.go_next_file()
        if not has_next:
            # end of folder reached
            self.stop_timer()
            messagebox.showinfo(
                title="End of folder",
                message="You have reached the end of the speedrun.",
            )
            self.abort_speedrun()
        return has_next

    def show_solution(self) -> None:
        self.target.main_viewcon.show_solution()

    def start_timer(self) -> None:
        self.target.main_timer.start()

    def stop_timer(self) -> None:
        self.target.main_timer.stop()

    def split_timer(self) -> None:
        self.target.main_timer.split()

    def mark_correct(self) -> None:
        self.target.main_problem_list_controller.set_status(pb.ProblemStatus.CORRECT)

    def mark_wrong(self) -> None:
        self.target.main_problem_list_controller.set_status(pb.ProblemStatus.WRONG)

    def mark_skip(self) -> None:
        self.target.main_problem_list_controller.set_status(pb.ProblemStatus.SKIP)

    def disable_solving(self) -> None:
        self.target.main_viewcon.disable_move_input()

    def enable_solving(self) -> None:
        self.target.main_viewcon.enable_move_input()

    def disable_move_navigation(self) -> None:
        self.target.main_viewcon.disable_move_navigation()

    def enable_move_navigation(self) -> None:
        self.target.main_viewcon.enable_move_navigation()

    def make_nav_pane_question(self, parent: tk.Widget) -> ttk.Frame:
        nav = ttk.Frame(parent)  # NavControlPane
        question_state = self._speedrun_states["question"]
        if not isinstance(question_state, Solving):
            logger.warning("speedrun question state missing")
            return nav
        btn_show_solution = ttk.Button(
            nav, text="Show solution", command=question_state.show_answer
        )
        btn_show_solution.grid(row=0, column=0, sticky="E", padx=5, pady=5)
        btn_skip = ttk.Button(nav, text="Skip", command=question_state.skip)
        btn_skip.grid(row=0, column=1, sticky="W", padx=5, pady=5)
        return nav

    def make_nav_pane_answer(self, parent: tk.Widget) -> ttk.Frame:
        nav = ttk.Frame(parent)  # NavControlPane
        answer_state = self._speedrun_states["answer"]
        if not isinstance(answer_state, ReviewAnswer):
            logger.warning("speedrun answer state missing")
            return nav
        btn_correct = ttk.Button(
            nav, text="Correct", command=answer_state.mark_correct_and_continue
        )
        btn_correct.grid(row=0, column=0, sticky="E", padx=5, pady=5)
        btn_wrong = ttk.Button(
            nav, text="Wrong", command=answer_state.mark_wrong_and_continue
        )
        btn_wrong.grid(row=0, column=1, sticky="W", padx=5, pady=5)
        return nav

    def make_nav_pane_solution(self, parent: tk.Widget) -> ttk.Frame:
        nav = ttk.Frame(parent)  # NavControlPane
        solution_state = self._speedrun_states["solution"]
        if not isinstance(solution_state, SolutionShown):
            logger.warning("speedrun solution state missing")
            return nav
        btn_continue = ttk.Button(
            nav, text="Next", command=solution_state.next_question
        )
        btn_continue.grid(row=0, column=0, padx=5, pady=5)
        return nav
