import tkinter as tk

from tkinter import ttk


class NavControls(ttk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
     
    def _add_btn_prev(self, text="< Prev"):
        return ttk.Button(self, text=text, command=self.controller.prev_file)
    
    def _add_btn_next(self, text="Next >"):
        return ttk.Button(self, text=text, command=self.controller.next_file)
    
    def _add_btn_toggle_solution(self, text="Show/hide solution"):
        return ttk.Button(
            self, text=text, command=self.controller.toggle_solution
        )
    
    def _add_btn_view_solution(self, text="Show solution"):
        return ttk.Button(
            self, text=text, command=self.controller.view_solution
        )
    
    def _add_btn_skip(self, text="Skip"):
        return ttk.Button(self, text=text, command=self.controller.skip)
    
    def _add_btn_correct(self, text="Correct"):
        return ttk.Button(self, text=text, command=self.controller.mark_correct)
    
    def _add_btn_wrong(self, text="Wrong"):
        return ttk.Button(self, text=text, command=self.controller.mark_wrong)
    
    def _add_chk_upside_down(self, text="Upside-down mode"):
        want_upside_down = tk.BooleanVar(value=False)
        return ttk.Checkbutton(
            self, text="Upside-down mode",
            command=lambda: self.controller.flip_board(want_upside_down.get()),
            variable=want_upside_down, onvalue=True, offvalue=False
        )


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
        return
    
    def show_sol_skip(self):
        self.btn_view_solution.grid()
        self.btn_skip.grid()
        self.btn_correct.grid_remove()
        self.btn_wrong.grid_remove()
        return