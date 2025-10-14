from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsumemi.src.tsumemi.speedrun_controller import SpeedrunController


class SpeedrunState:
    def __init__(self, controller: SpeedrunController) -> None:
        self.controller = controller

    def on_entry(self) -> None:
        return

    def on_exit(self) -> None:
        return


class Solving(SpeedrunState):
    def __init__(self, controller: SpeedrunController) -> None:
        SpeedrunState.__init__(self, controller)

    def on_entry(self) -> None:
        self.controller.start_timer()
        self.controller.disable_move_navigation()

    def skip(self) -> None:
        self.controller.split_timer()
        self.controller.mark_skip()
        if self.controller.go_next_question():
            self.controller.go_to_state("question")

    def show_answer(self) -> None:
        self.controller.go_to_state("answer")

    def pause(self) -> None:
        self.controller.go_to_state("pause")


class Paused(SpeedrunState):
    # Should it disable showing solution?
    def on_entry(self) -> None:
        self.controller.stop_timer()
        self.controller.disable_solving()

    def on_exit(self) -> None:
        self.controller.enable_solving()

    def unpause(self) -> None:
        self.controller.go_to_state("question")


class ReviewAnswer(SpeedrunState):
    def on_entry(self) -> None:
        self.controller.split_timer()
        self.controller.stop_timer()
        self.controller.show_solution()
        self.controller.enable_move_navigation()

    def mark_correct_and_continue(self) -> None:
        self.controller.mark_correct()
        if self.controller.go_next_question():
            self.controller.go_to_state("question")

    def mark_wrong_and_continue(self) -> None:
        self.controller.mark_wrong()
        if self.controller.go_next_question():
            self.controller.go_to_state("question")


class SolutionShown(SpeedrunState):
    def on_entry(self) -> None:
        self.controller.split_timer()
        self.controller.stop_timer()
        self.controller.show_solution()
        self.controller.enable_move_navigation()

    def next_question(self) -> None:
        if self.controller.go_next_question():
            self.controller.go_to_state("question")


class NotInSpeedrun(SpeedrunState):
    # Default state
    pass
