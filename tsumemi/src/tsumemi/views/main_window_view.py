from __future__ import annotations

import functools
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.views.views import NavControlFrame, SolutionLabel, SpeedrunFrame

if TYPE_CHECKING:
    from typing import Callable, Optional
    import tsumemi.src.tsumemi.board_gui.board_canvas as bc
    import tsumemi.src.tsumemi.game.game_controller as gamecon
    import tsumemi.src.tsumemi.timer_controller as timecon
    from tsumemi.src.tsumemi.kif_browser_gui import RootController
    from tsumemi.src.tsumemi.views.main_window_view_controller import MainWindowViewController
    from tsumemi.src.tsumemi.movelist.movelist_view import MovelistFrame
    from tsumemi.src.tsumemi.problem_list.problem_list_view import ProblemListPane


class MainWindowView(ttk.Frame):
    def __init__(self,
            root: tk.Tk,
            root_controller: RootController,
            viewcon: MainWindowViewController,
        ) -> None:
        ttk.Frame.__init__(self, root)
        self.controller: RootController = root_controller
        self.viewcon = viewcon
        # grid itself to the window it is in
        self.grid(row=0, column=0, sticky="NSEW", padx=10, pady=10)
        self.pwn_main = tk.PanedWindow(
            self,
            orient="horizontal",
            sashrelief="groove",
            sashwidth=5
        )
        self.pane_1 = ttk.Frame(self.pwn_main)
        self.pane_2 = ttk.Frame(self.pwn_main)
        self.pane_3 = ttk.Frame(self.pwn_main)
        self.pwn_main.add(self.pane_1, stretch="always")
        self.pwn_main.add(self.pane_2, stretch="always")
        self.pwn_main.add(self.pane_3, stretch="always")
        self.pwn_main.grid(row=0, column=0, sticky="NSEW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Pane 1
        self.movelist_frame: MovelistFrame
        self.movelist_frame = (
            root_controller
            .main_game
            .movelist_controller
            .make_movelist_view(self.pane_1)
        )
        self.pane_1.grid_columnconfigure(0, weight=1)
        self.pane_1.grid_rowconfigure(0, weight=1)
        self.movelist_frame.grid(row=0, column=0, sticky="NSEW", padx=10, pady=10)

        # Pane 2
        self.board_frame: gamecon.NavigableGameFrame
        self.board_canvas: bc.BoardCanvas
        self.board_frame, self.board_canvas = (
            root_controller
            .main_game
            .make_navigable_view(
                parent=self.pane_2, skin_settings=root_controller.skin_settings
            )
        )
        self.lbl_solution: SolutionLabel = SolutionLabel(
            parent=self.pane_2,
            height=3,
            justify="left",
            wraplength=600,
        )
        self.frm_nav_control = NavControlFrame(
            self.pane_2,
            self.viewcon.flip_main_board
        )
        self.pane_2.grid_columnconfigure(0, weight=1)
        self.pane_2.grid_rowconfigure(0, weight=4)
        self.pane_2.grid_rowconfigure(1, weight=1)
        self.pane_2.grid_rowconfigure(2, weight=0)
        self.board_frame.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        self.lbl_solution.grid(row=1, column=0, sticky="W", padx=5, pady=5)
        self.frm_nav_control.grid(row=2, column=0, sticky="NSEW")
        self.frm_nav_control.grid_columnconfigure(0, weight=1)
        self.frm_nav_control.grid_rowconfigure(0, weight=1)
        self.update_nav_control_pane()

        # Pane 3
        self.main_timer_view: timecon.TimerPane = (
            root_controller
            .main_timer
            .make_timer_pane(parent=self.pane_3)
        )
        self.problem_list_pane: ProblemListPane = (
            root_controller
            .main_problem_list
            .make_problem_list_pane(parent=self.pane_3)
        )
        self.speedrun_frame = SpeedrunFrame(
            self.pane_3,
            self.controller.start_speedrun,
            self.controller.abort_speedrun,
        )
        self.pane_3.grid_columnconfigure(0, weight=1)
        self.pane_3.grid_rowconfigure(0, weight=4)
        self.pane_3.grid_rowconfigure(1, weight=1)
        self.pane_3.grid_rowconfigure(2, weight=0)
        self.problem_list_pane.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        self.main_timer_view.grid(row=1, column=0)
        self.speedrun_frame.grid(row=2, column=0)
        return

    def update_nav_control_pane(self,
            nav_pane_constructor: Optional[Callable[[tk.Widget], ttk.Frame]] = None
        ) -> None:
        if nav_pane_constructor is None:
            nav_pane_constructor = functools.partial(
                self.frm_nav_control.make_nav_pane_normal,
                callable_prev=self.controller.go_prev_file,
                callable_toggle_solution=self.viewcon.toggle_solution,
                callable_next=self.controller.go_next_file,
            )
        self.frm_nav_control.set_new_nav_controls(nav_pane_constructor)
        return
