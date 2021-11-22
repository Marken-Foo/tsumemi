from __future__ import annotations

import tkinter as tk

from tkinter import font, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    import tsumemi.src.tsumemi.board_canvas as bc
    import tsumemi.src.tsumemi.game_controller as gamecon
    import tsumemi.src.tsumemi.img_handlers as imghand
    import tsumemi.src.tsumemi.problem_list_controller as plistcon
    import tsumemi.src.tsumemi.timer_controller as timecon
    from tsumemi.src.tsumemi.kif_browser_gui import RootController


class MainWindowView(ttk.Frame):
    def __init__(self, root: tk.Tk, root_controller: RootController) -> None:
        super().__init__(root)
        self.controller: RootController = root_controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="NSEW")
        
        self.board_frame: gamecon.NavigableGameFrame
        self.board_canvas: bc.BoardCanvas
        self.board_frame, self.board_canvas = (
            root_controller
            .main_game
            .make_navigable_view(parent=self)
        )
        
        self.main_timer_view: timecon.TimerPane = (
            root_controller
            .main_timer
            .make_timer_pane(parent=self)
        )
        self.problem_list_pane: plistcon.ProblemListPane = (
            root_controller
            .main_problem_list
            .make_problem_list_pane(parent=self)
        )
        self.lbl_solution: SolutionLabel = SolutionLabel(parent=self,
            height=3,
            justify="left",
            wraplength=600,
        )
        
        self.nav_control_pane = ttk.Frame(self)
        self.nav_controls = ttk.Frame(self.nav_control_pane)
        want_upside_down = tk.BooleanVar(value=False)
        self.chk_upside_down = ttk.Checkbutton(
            self.nav_control_pane,
            text="Upside-down mode",
            command=lambda: self.controller.mainframe.flip_main_board(want_upside_down.get()),
            variable=want_upside_down, onvalue=True, offvalue=False
        )
        
        self.speedrun_frame = ttk.Frame(self)
        self.btn_speedrun: ttk.Button = ttk.Button(self.speedrun_frame, text="Start speedrun",
            command=self.controller.start_speedrun
        )
        self.btn_abort_speedrun: ttk.Button = ttk.Button(self.speedrun_frame, text="Abort speedrun",
            command=self.controller.abort_speedrun
        )
        return
    
    def apply_skins(self, settings: imghand.SkinSettings) -> None:
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
    
    def toggle_solution(self, event: Optional[tk.Event] = None) -> None:
        self.lbl_solution.toggle_solution()
        return
    
    def set_solution(self, solution_text: str) -> None:
        self.lbl_solution.set_solution_text(solution_text)
        return
    
    def make_nav_pane_normal(self, parent):
        nav = ttk.Frame(parent)
        btn_prev = ttk.Button(nav,
            text="< Prev",
            command=self.controller.go_prev_file
        )
        btn_toggle_solution = ttk.Button(nav,
            text="Show/hide solution",
            command=self.controller.toggle_solution
        )
        btn_next = ttk.Button(nav,
            text="Next >",
            command=self.controller.go_next_file
        )
        btn_prev.grid(
            row=0, column=0, sticky="E",
            padx=5, pady=5
        )
        btn_toggle_solution.grid(
            row=0, column=1, sticky="S",
            padx=5, pady=5
        )
        btn_next.grid(
            row=0, column=2, sticky="W",
            padx=5, pady=5
        )
        return nav
    
    def _grid_nav_control_pane(self, pane) -> None:
        pane.grid(
            row=0, column=0
        )
        self.chk_upside_down.grid(
            row=1, column=0
        )
        return
    
    def update_nav_control_pane(self, nav_pane_constructor) -> None:
        new_nav_controls = nav_pane_constructor(self.nav_control_pane)
        self._grid_nav_control_pane(new_nav_controls)
        self.nav_controls.grid_forget()
        self.nav_controls = new_nav_controls
        return
    
    def grid_items_normal(self) -> None:
        self.board_frame.grid_columnconfigure(0, weight=1)
        self.board_frame.grid_rowconfigure(0, weight=1)
        self.main_timer_view.grid_columnconfigure(0, weight=0)
        self.main_timer_view.grid_rowconfigure(0, weight=0)
        self.problem_list_pane.grid_columnconfigure(0, weight=1)
        self.problem_list_pane.grid_rowconfigure(0, weight=1)
        
        self.board_frame.grid(
             row=0, column=0,
            sticky="NSEW", padx=5, pady=5
        )
        self.problem_list_pane.grid(
            row=0, column=1,
            sticky="NSEW", padx=5, pady=5
        )
        self.lbl_solution.grid(
            row=1, column=0,
            sticky="W", padx=5, pady=5
        )
        self.main_timer_view.grid(
            row=1, column=1,
        )
        self.nav_control_pane.grid(
            row=2, column=0
        )
        self.update_nav_control_pane(self.make_nav_pane_normal)
        self._grid_nav_control_pane(self.nav_controls)
        self.speedrun_frame.grid(
            row=2, column=1,
        )
        self.btn_speedrun.grid(row=0, column=0)
        self.btn_abort_speedrun.grid(row=0, column=1)
        self.btn_abort_speedrun.config(state="disabled")
        return


class SolutionLabel(tk.Label):
    """Label to display, show, and hide problem solutions.
    """
    def __init__(self, parent: tk.Widget, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
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
    
    def toggle_solution(self, event: Optional[tk.Event] = None) -> None:
        if self.is_solution_shown:
            self.hide_solution()
        else:
            self.show_solution()
        return
