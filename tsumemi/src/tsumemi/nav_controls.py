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
        
        self._navcons = {
            "free" : FreeModeNavControls(
                parent=self, controller=root_controller,
            ),
            "speedrun" : SpeedrunNavControls(
                parent=self, controller=root_controller,
            )
        }
        for navcon in self._navcons.values():
            navcon.grid(row=2, column=0)
            navcon.grid_remove()
        self.nav_controls: NavControls = self._navcons["free"]
        
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
        self.nav_controls.grid(
            row=2, column=0
        )
        self.speedrun_frame.grid(
            row=2, column=1,
        )
        self.btn_speedrun.grid(row=0, column=0)
        self.btn_abort_speedrun.grid(row=0, column=1)
        self.btn_abort_speedrun.config(state="disabled")
        return


class NavControls(ttk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
     
    def _add_btn_prev(self, text="< Prev"):
        return ttk.Button(self, text=text,
            command=self.controller.go_prev_file
        )
    
    def _add_btn_next(self, text="Next >"):
        return ttk.Button(self, text=text,
            command=self.controller.go_next_file
        )
    
    def _add_btn_toggle_solution(self, text="Show/hide solution"):
        return ttk.Button(self, text=text,
            command=self.controller.toggle_solution
        )
    
    def _add_btn_view_solution(self, text="Show solution"):
        return ttk.Button(self, text=text,
            command=self.controller.speedrun_controller._speedrun_states["question"].show_answer
        )
    
    def _add_btn_skip(self, text="Skip"):
        return ttk.Button(self, text=text,
            command=self.controller.speedrun_controller._speedrun_states["question"].skip
        )
    
    def _add_btn_correct(self, text="Correct"):
        return ttk.Button(self, text=text,
            command=self.controller.speedrun_controller._speedrun_states["answer"].mark_correct_and_continue
        )
    
    def _add_btn_wrong(self, text="Wrong"):
        return ttk.Button(self, text=text,
            command=self.controller.speedrun_controller._speedrun_states["answer"].mark_wrong_and_continue
        )
    
    def _add_btn_continue_speedrun(self, text="Next"):
        return ttk.Button(self, text=text,
            command=self.controller.speedrun_controller._speedrun_states["solution"].next_question
        )
    
    def _add_chk_upside_down(self, text="Upside-down mode"):
        want_upside_down = tk.BooleanVar(value=False)
        return ttk.Checkbutton(self, text=text,
            command=lambda: self.controller.mainframe.flip_main_board(want_upside_down.get()),
            variable=want_upside_down, onvalue=True, offvalue=False
        )
    
    def show_correct_wrong(self):
        pass
    
    def show_sol_skip(self):
        pass
    
    def show_continue(self):
        pass


class FreeModeNavControls(NavControls):
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, controller, *args, **kwargs)
        # Make buttons to navigate, show/hide solution, upside-down mode
        btn_prev = self._add_btn_prev()
        btn_prev.grid(row=0, column=0, sticky="E")
        btn_toggle_solution = self._add_btn_toggle_solution()
        btn_toggle_solution.grid(row=0, column=1, sticky="S")
        btn_next = self._add_btn_next()
        btn_next.grid(row=0, column=2, sticky="W")
        chk_upside_down = self._add_chk_upside_down()
        chk_upside_down.grid(row=1, column=0, columnspan=3)
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)
        return


class SpeedrunNavControls(NavControls):
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, controller, *args, **kwargs)
        # Initialise all nav options
        self.btn_view_solution = self._add_btn_view_solution()
        self.btn_view_solution.grid(row=0, column=0, sticky="E")
        self.btn_skip = self._add_btn_skip()
        self.btn_skip.grid(row=0, column=1, sticky="W")
        self.btn_correct = self._add_btn_correct()
        self.btn_correct.grid(row=0, column=0, sticky="E")
        self.btn_wrong = self._add_btn_wrong()
        self.btn_wrong.grid(row=0, column=1, sticky="W")
        self.btn_continue_speedrun = self._add_btn_continue_speedrun()
        self.btn_continue_speedrun.grid(row=0, column=0)
        self.chk_upside_down = self._add_chk_upside_down()
        self.chk_upside_down.grid(row=1, column=0, columnspan=3)
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)
            
        self.show_sol_skip() # Hide only after calling grid_configure
        return
     
    def show_correct_wrong(self):
        self.btn_view_solution.grid_remove()
        self.btn_skip.grid_remove()
        self.btn_correct.grid()
        self.btn_wrong.grid()
        self.btn_continue_speedrun.grid_remove()
        return
    
    def show_sol_skip(self):
        self.btn_view_solution.grid()
        self.btn_skip.grid()
        self.btn_correct.grid_remove()
        self.btn_wrong.grid_remove()
        self.btn_continue_speedrun.grid_remove()
        return
    
    def show_continue(self):
        self.btn_view_solution.grid_remove()
        self.btn_skip.grid_remove()
        self.btn_correct.grid_remove()
        self.btn_wrong.grid_remove()
        self.btn_continue_speedrun.grid()
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
