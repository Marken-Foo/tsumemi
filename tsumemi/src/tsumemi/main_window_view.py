from __future__ import annotations

import tkinter as tk

from tkinter import font, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional
    import tsumemi.src.tsumemi.board_gui.board_canvas as bc
    import tsumemi.src.tsumemi.game.game_controller as gamecon
    import tsumemi.src.tsumemi.timer_controller as timecon
    from tsumemi.src.tsumemi import skins
    from tsumemi.src.tsumemi.kif_browser_gui import RootController
    from tsumemi.src.tsumemi.movelist.movelist_view import MovelistFrame
    from tsumemi.src.tsumemi.problem_list.problem_list_view import ProblemListPane


class MainWindowView(ttk.Frame):
    def __init__(self, root: tk.Tk, root_controller: RootController) -> None:
        ttk.Frame.__init__(self, root)
        self.controller: RootController = root_controller
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
        self.lbl_solution: SolutionLabel = SolutionLabel(parent=self.pane_2,
            height=3,
            justify="left",
            wraplength=600,
        )
        self.nav_control_pane = ttk.Frame(self.pane_2)
        self.nav_controls = ttk.Frame(self.nav_control_pane)
        want_upside_down = tk.BooleanVar(value=False)
        self.chk_upside_down = ttk.Checkbutton(
            self.nav_control_pane,
            text="Upside-down mode",
            command=lambda: self.controller.mainframe.flip_main_board(want_upside_down.get()),
            variable=want_upside_down, onvalue=True, offvalue=False
        )
        self.pane_2.grid_columnconfigure(0, weight=1)
        self.pane_2.grid_rowconfigure(0, weight=4)
        self.pane_2.grid_rowconfigure(1, weight=1)
        self.pane_2.grid_rowconfigure(2, weight=0)
        self.board_frame.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        self.lbl_solution.grid(row=1, column=0, sticky="W", padx=5, pady=5)
        self.nav_control_pane.grid(row=2, column=0, sticky="NSEW")
        self.nav_control_pane.grid_columnconfigure(0, weight=1)
        self.nav_control_pane.grid_rowconfigure(0, weight=1)
        self.update_nav_control_pane(self.make_nav_pane_normal)
        self._grid_nav_control_pane(self.nav_controls)

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
        self.movelist_frame.refresh_content()
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

    def hide_solution(self) -> None:
        self.lbl_solution.hide_solution()
        return

    def show_solution(self) -> None:
        self.lbl_solution.show_solution()
        return

    def toggle_solution(self, _event: Optional[tk.Event] = None) -> None:
        self.lbl_solution.toggle_solution()
        return

    def set_solution(self, solution_text: str) -> None:
        self.lbl_solution.set_solution_text(solution_text)
        return

    def set_btns_allow_abort_speedrun(self) -> None:
        self.speedrun_frame.allow_abort_speedrun()
        return

    def set_btns_allow_start_speedrun(self) -> None:
        self.speedrun_frame.allow_start_speedrun()
        return

    def make_nav_pane_normal(self, parent: tk.Widget) -> ttk.Frame:
        nav = ttk.Frame(parent)
        btn_prev = ttk.Button(nav,
            text="< Prev",
            command=self.controller.go_prev_file
        )
        btn_prev.grid(
            row=0, column=0, sticky="E",
            padx=5, pady=5
        )
        btn_toggle_solution = ttk.Button(nav,
            text="Show/hide solution",
            command=self.toggle_solution
        )
        btn_toggle_solution.grid(
            row=0, column=1, sticky="S",
            padx=5, pady=5
        )
        btn_next = ttk.Button(nav,
            text="Next >",
            command=self.controller.go_next_file
        )
        btn_next.grid(
            row=0, column=2, sticky="W",
            padx=5, pady=5
        )
        return nav

    def _grid_nav_control_pane(self, pane: ttk.Frame) -> None:
        pane.grid_columnconfigure(0, weight=1)
        pane.grid_rowconfigure(0, weight=0)
        pane.grid_rowconfigure(0, weight=0)
        pane.grid(
            row=0, column=0
        )
        self.chk_upside_down.grid(
            row=1, column=0
        )
        return

    def update_nav_control_pane(self,
            nav_pane_constructor: Callable[[tk.Widget], ttk.Frame]
        ) -> None:
        new_nav_controls = nav_pane_constructor(self.nav_control_pane)
        self._grid_nav_control_pane(new_nav_controls)
        self.nav_controls.grid_forget()
        self.nav_controls = new_nav_controls
        return


class SpeedrunFrame(ttk.Frame):
    """Frame containing speedrun controls.
    """
    def __init__(self,
            parent: tk.Widget,
            start_speedrun: Callable[[], None],
            abort_speedrun: Callable[[], None],
        ) -> None:
        ttk.Frame.__init__(self, parent)
        self.btn_speedrun: ttk.Button = ttk.Button(
            self,
            text="Start speedrun",
            command=start_speedrun
        )
        self.btn_abort_speedrun: ttk.Button = ttk.Button(
            self,
            text="Abort speedrun",
            command=abort_speedrun
        )
        self.btn_speedrun.grid(row=0, column=0)
        self.btn_abort_speedrun.grid(row=0, column=1)
        self.btn_abort_speedrun.config(state="disabled")
        return

    def allow_start_speedrun(self):
        self.btn_speedrun.config(state="normal")
        self.btn_abort_speedrun.config(state="disabled")
        return

    def allow_abort_speedrun(self):
        self.btn_speedrun.config(state="disabled")
        self.btn_abort_speedrun.config(state="normal")
        return


class SolutionLabel(tk.Label):
    """Label to display, show, and hide problem solutions.
    """
    def __init__(self, parent: tk.Widget, *args: Any, **kwargs: Any) -> None:
        tk.Label.__init__(self, parent, *args, **kwargs)
        self.is_solution_shown: bool = True
        self.solution_text: str = "Open a folder of problems to display."
        self.textvar: tk.StringVar = tk.StringVar(value=self.solution_text)
        self["textvariable"] = self.textvar

        defaultfont = font.Font(font=self["font"])
        typeface = defaultfont["family"]
        fontsize = defaultfont["size"]
        self.config(font=(typeface, fontsize+2))
        return

    def set_solution_text(self, text: str) -> None:
        self.solution_text = text
        return

    def hide_solution(self) -> None:
        self.textvar.set("[solution hidden]")
        self.is_solution_shown = False
        return

    def show_solution(self) -> None:
        self.textvar.set(self.solution_text)
        self.is_solution_shown = True
        return

    def toggle_solution(self, _event: Optional[tk.Event] = None) -> None:
        if self.is_solution_shown:
            self.hide_solution()
        else:
            self.show_solution()
        return
