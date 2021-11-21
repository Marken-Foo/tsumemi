from __future__ import annotations

import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    import tsumemi.src.tsumemi.img_handlers as imghand
    from tsumemi.src.tsumemi.kif_browser_gui import RootController


class MainWindowView(ttk.Frame):
    def __init__(self, root: tk.Tk, root_controller: RootController) -> None:
        super().__init__(root)
        self.controller = root_controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid(column=0, row=0, sticky="NSEW")
        
        self._navcons = {
            "free" : FreeModeNavControls(
                parent=self, controller=root_controller,
            ),
            "speedrun" : SpeedrunNavControls(
                parent=self, controller=root_controller,
            )
        }
        for navcon in self._navcons.values():
            navcon.grid(column=0, row=2)
            navcon.grid_remove()
        self.nav_controls = self._navcons["free"]
        
        self.speedrun_frame = ttk.Frame(self)
        self.btn_speedrun = ttk.Button(self.speedrun_frame, text="Start speedrun",
            command=self.controller.start_speedrun
        )
        self.btn_abort_speedrun = ttk.Button(self.speedrun_frame, text="Abort speedrun",
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
    
    def add_board_frame(self, constructor, *args, **kwargs) -> None:
        self.board_frame, self.board_canvas = constructor(
            parent=self, *args, **kwargs
        )
        return
    
    def add_timer_view(self, constructor, *args, **kwargs) -> None:
        self.main_timer_view = constructor(parent=self, *args, **kwargs)
        return
    
    def add_problem_list_pane(self, constructor, *args, **kwargs) -> None:
        self.problem_list_pane = constructor(parent=self, *args, **kwargs)
        return
    
    def add_solution_pane(self, constructor, *args, **kwargs) -> None:
        self.lbl_solution = constructor(
            parent=self,
            height=3,
            justify="left",
            wraplength=600,
            *args, **kwargs
        )
        return
    
    def grid_items_normal(self) -> None:
        self.board_frame.grid_columnconfigure(0, weight=1)
        self.board_frame.grid_rowconfigure(0, weight=1)
        self.main_timer_view.grid_columnconfigure(0, weight=0)
        self.main_timer_view.grid_rowconfigure(0, weight=0)
        self.problem_list_pane.grid_columnconfigure(0, weight=1)
        self.problem_list_pane.grid_rowconfigure(0, weight=1)
        
        self.board_frame.grid(column=0, row=0, sticky="NSEW")
        self.board_frame.grid_configure(padx=5, pady=5)
        self.lbl_solution.grid(column=0, row=1, sticky="W")
        self.lbl_solution.grid_configure(padx=5, pady=5)
        self.nav_controls.grid()
        self.main_timer_view.grid(column=1, row=1)
        self.problem_list_pane.grid(column=1, row=0, sticky="NSEW")
        self.problem_list_pane.grid_configure(padx=5, pady=5)
        self.speedrun_frame.grid(column=1, row=2)
        self.btn_speedrun.grid(column=0, row=0)
        self.btn_abort_speedrun.grid(column=1, row=0)
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
        btn_prev.grid(column=0, row=0, sticky="E")
        btn_toggle_solution = self._add_btn_toggle_solution()
        btn_toggle_solution.grid(column=1, row=0, sticky="S")
        btn_next = self._add_btn_next()
        btn_next.grid(column=2, row=0, sticky="W")
        chk_upside_down = self._add_chk_upside_down()
        chk_upside_down.grid(column=0, row=1, columnspan=3)
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)
        return


class SpeedrunNavControls(NavControls):
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, controller, *args, **kwargs)
        # Initialise all nav options
        self.btn_view_solution = self._add_btn_view_solution()
        self.btn_view_solution.grid(column=0, row=0, sticky="E")
        self.btn_skip = self._add_btn_skip()
        self.btn_skip.grid(column=1, row=0, sticky="W")
        self.btn_correct = self._add_btn_correct()
        self.btn_correct.grid(column=0, row=0, sticky="E")
        self.btn_wrong = self._add_btn_wrong()
        self.btn_wrong.grid(column=1, row=0, sticky="W")
        self.btn_continue_speedrun = self._add_btn_continue_speedrun()
        self.btn_continue_speedrun.grid(column=0, row=0)
        self.chk_upside_down = self._add_chk_upside_down()
        self.chk_upside_down.grid(column=0, row=1, columnspan=3)
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