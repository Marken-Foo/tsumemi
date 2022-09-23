from __future__ import annotations

from typing import TYPE_CHECKING

from tsumemi.src.tsumemi import skins
from tsumemi.src.tsumemi.main_window_view import MainWindowView

if TYPE_CHECKING:
    import tkinter as tk
    from tkinter import ttk
    from typing import Callable, Optional
    from tsumemi.src.tsumemi.kif_browser_gui import RootController


class MainWindowViewController:
    """Controller for the view of the main window. Is aware of the
    entire view structure of the main window.
    """
    def __init__(self, root: tk.Tk, root_controller: RootController) -> None:
        self.controller = root_controller
        self.view = MainWindowView(root, root_controller, self)
        self.board_canvas = self.view.board_canvas
        self.problems_view = self.view.problem_list_pane.tvwfrm_problems
        self.solution_view = self.view.lbl_solution
        self.timer_view = self.view.main_timer_view
        return

    def apply_skins(self, settings: skins.SkinSettings) -> None:
        piece_skin, board_skin, komadai_skin = settings.get()
        self.board_canvas.apply_piece_skin(piece_skin)
        self.board_canvas.apply_board_skin(board_skin)
        self.board_canvas.apply_komadai_skin(komadai_skin)
        self.refresh_main_board()
        return

    def refresh_main_board(self) -> None:
        self.board_canvas.draw()
        return

    def flip_main_board(self, want_upside_down: bool) -> None:
        self.board_canvas.flip_board(want_upside_down)
        return

    def refresh_move_list(self) -> None:
        self.view.movelist_frame.refresh_content()
        return

    def disable_problem_list_input(self) -> None:
        self.problems_view.disable_input()
        return

    def enable_problem_list_input(self) -> None:
        self.problems_view.enable_input()
        return

    def disable_move_input(self) -> None:
        move_input_handler = self.board_canvas.move_input_handler
        if move_input_handler is not None:
            move_input_handler.disable()
        return

    def enable_move_input(self) -> None:
        move_input_handler = self.board_canvas.move_input_handler
        if move_input_handler is not None:
            move_input_handler.enable()
        return

    def disable_move_navigation(self) -> None:
        self.view.movelist_frame.disable_display()
        self.view.board_frame.disable_buttons()
        return

    def enable_move_navigation(self) -> None:
        self.view.movelist_frame.enable_display()
        self.view.board_frame.enable_buttons()
        return

    def hide_solution(self) -> None:
        self.solution_view.hide_solution()
        return

    def show_solution(self) -> None:
        self.solution_view.show_solution()
        return

    def toggle_solution(self, _event: Optional[tk.Event] = None) -> None:
        self.solution_view.toggle_solution()
        return

    def set_solution(self, solution_text: str) -> None:
        self.solution_view.set_solution_text(solution_text)
        return

    def allow_only_pause_timer(self) -> None:
        self.timer_view.allow_only_pause()
        return

    def allow_all_timer(self) -> None:
        self.timer_view.allow_all()
        return

    def set_btns_allow_abort_speedrun(self) -> None:
        self.view.speedrun_frame.allow_abort_speedrun()
        return

    def set_btns_allow_start_speedrun(self) -> None:
        self.view.speedrun_frame.allow_start_speedrun()
        return

    def set_normal_nav_pane(self) -> None:
        self.view.update_nav_control_pane()
        return

    def set_nav_pane(self,
            nav_pane_constructor: Callable[[tk.Widget], ttk.Frame]
        ) -> None:
        self.view.update_nav_control_pane(nav_pane_constructor)
        return
