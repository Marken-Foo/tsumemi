import os
import re
import tkinter as tk

from enum import Enum
from tkinter import filedialog, messagebox, ttk

import kif_parser
from board_canvas import BoardCanvas
from split_timer import SplitTimer


class Menubar(tk.Menu):
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        
        menu_file = tk.Menu(self)
        self.add_cascade(menu=menu_file, label="File")
        menu_file.add_command(
            label="Open folder...",
            command=self.controller.open_folder,
            accelerator="Ctrl+O",
            underline=0
        )
        parent["menu"] = self
        
        menu_help = tk.Menu(self)
        self.add_cascade(menu=menu_help, label="Help")
        #menu_help.add_command(label="Help", command=None)
        menu_help.add_command(
            label="About kif-browser",
            command=lambda: messagebox.showinfo(
                title="About kif-browser",
                message="Written in Python 3 for the shogi community. KIF files sold separately."
            )
        )
        return


class NavControls(ttk.Frame):
    #TODO: Refactoring class to enable subclassing to build different layouts for NavControl frame, accomodating different modes (planned: regular "free" browsing mode, and speedrun mode)
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


class TimerModule(ttk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        self.timer = SplitTimer()
        
        # Basic timer
        self.timer = SplitTimer()
        self.timer_display_str = tk.StringVar(value="00:00:00")
        self.timer_display = ttk.Label(
            self, textvariable=self.timer_display_str
        )
        self.timer_display.grid(
            column=0, row=0, columnspan=3
        )
        ttk.Button(
            self, text="Start/stop timer",
            command=self.toggle_timer
        ).grid(
            column=0, row=1
        )
        ttk.Button(
            self, text="Reset timer",
            command=self.reset_timer
        ).grid(
            column=1, row=1
        )
        ttk.Button(
            self, text="Split",
            command=self.controller.split_timer
        ).grid(
            column=2, row=1
        )
    
    def start_timer(self):
        self.timer.start()
        self.refresh_timer()
        return
        
    def stop_timer(self):
        self.timer.stop()
        return
    
    def toggle_timer(self):
        if self.timer.is_running:
            self.stop_timer()
        else:
            self.start_timer()
        return
    
    def reset_timer(self):
        self.timer.stop()
        self.timer.reset()
        self.refresh_timer()
        return
    
    def refresh_timer(self):
        self.timer_display_str.set(SplitTimer.sec_to_str(self.timer.read()))
        if self.timer.is_running:
            self.timer_display.after(40, self.refresh_timer)
        return


class ProblemListView(ttk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        
        # Display problem list as Treeview
        self.tvw = ttk.Treeview(
            self, columns=("filename", "time"), show="headings"
        )
        self.tvw.column("filename")
        self.tvw.heading("filename", text="Problem")
        self.tvw.heading("time", text="Time")
        self.tvw.grid(column=0, row=0, sticky="NSEW")
        
        # Make scrollbar
        self.scrollbar_tvw = ttk.Scrollbar(
            self, orient=tk.VERTICAL,
            command=self.tvw.yview
        )
        self.scrollbar_tvw.grid(column=1, row=0, sticky="NS")
        self.tvw["yscrollcommand"] = self.scrollbar_tvw.set
    
    def set_time(self, idx, time_str):
        # Set time column for item at given index
        item = self.tvw.get_children()[idx]
        self.tvw.set(item, column="time", value=time_str)
        return


class ProblemStatus(Enum):
    NONE = 0; CORRECT = 1; WRONG = 2; SKIP = 3


class Problem:
    '''Data class representing one tsume problem.'''
    def __init__(self, filename):
        self.filename = filename
        self.time = None
        self.status = ProblemStatus.NONE
        return


class MainWindow:
    '''Class encapsulating the window to display the kif.'''
    # Reference to tk.Tk() root object
    master = None
    # Member variables that deal with the file system
    directory = None # not in use
    problems = []
    curr_prob_idx = None
    curr_prob = None
    # Other member variables
    kif_reader = kif_parser.TsumeKifReader()
    is_solution_shown = False
    
    # eventually, refactor menu labels and dialog out into a constant namespace
    def __init__(self, master):
        # tkinter stuff, set up the main window
        self.master = master
        self.master.option_add("*tearOff", False)
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.title("KIF folder browser")
        
        self.mainframe = ttk.Frame(self.master)
        self.mainframe.grid(column=0, row=0, sticky="NSEW")
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.columnconfigure(1, weight=1)
        self.mainframe.columnconfigure(2, weight=1)
        self.mainframe.rowconfigure(0, weight=1)
        
        # Make menubar
        self.menubar = Menubar(parent=self.master, controller=self)
        
        # Make canvas for board
        self.boardWrapper = ttk.Frame(self.mainframe)
        self.boardWrapper.grid(column=0, row=0, sticky="NSEW")
        self.boardWrapper.columnconfigure(0, weight=1)
        self.boardWrapper.rowconfigure(0, weight=1)
        
        self.board = BoardCanvas(
            parent=self.boardWrapper, controller=self,
            width=BoardCanvas.canvas_width, height=BoardCanvas.canvas_height,
            bg="white"
        )
        self.board.grid(column=0, row=0, sticky="NSEW")
        self.board.bind("<Configure>", self.board.on_resize)
        
        # Initialise solution text
        self.solution = tk.StringVar(value="Open a folder of problems to display.")
        ttk.Label(
            self.mainframe, textvariable=self.solution,
            justify="left", wraplength=self.board.canvas_width
        ).grid(
            column=0, row=1, sticky="W"
        )
        
        # Make buttons to navigate, show/hide solution, upside-down mode
        self.nav_controls = SpeedrunNavControls(parent=self.mainframe, controller=self)
        self.nav_controls.grid(column=0, row=2)
        
        # Timer controls and display
        self.timer_controls = TimerModule(parent=self.mainframe, controller=self)
        self.timer_controls.grid(column=1, row=1)
        self.timer_controls.columnconfigure(0, weight=0)
        self.timer_controls.rowconfigure(0, weight=0)
        
        # Problem list
        self.problem_list_view = ProblemListView(parent=self.mainframe, controller=self)
        self.problem_list_view.grid(column=1, row=0)
        
        # Keyboard shortcuts
        self.master.bind("<Key-h>", self.toggle_solution)
        self.master.bind("<Left>", self.prev_file)
        self.master.bind("<Right>", self.next_file)
        self.master.bind("<Control_L><Key-o>", self.open_folder)
        self.master.bind("<Control_R><Key-o>", self.open_folder)
        return
        
    def display_problem(self):
        # Parse current problem and draw problem to canvas
        # Try any likely encodings for the KIF files
        encodings = ["cp932", "utf-8"]
        for e in encodings:
            try:
                with open(self.curr_prob.filename, "r", encoding=e) as kif:
                    self.kif_reader.parse_kif(kif)
            except UnicodeDecodeError:
                pass
            else:
                break
        self.board.draw()
        self.hide_solution()
        self.master.title("KIF folder browser - " + str(self.curr_prob.filename))
        return
    
    def hide_solution(self):
        self.solution.set("[solution hidden]")
        self.is_solution_shown = False
        return
    
    def show_solution(self):
        solution = "　".join(self.kif_reader.moves)
        self.solution.set(solution)
        self.is_solution_shown = True
        return
    
    def toggle_solution(self, event=None):
        if self.is_solution_shown:
            self.hide_solution()
        else:
            self.show_solution()
        return
    
    def set_directory(self, directory):
        # Update internal variables. Kif reader not updated.
        self.directory = directory
        with os.scandir(directory) as it:
            self.problems = [
                Problem(os.path.join(directory, entry.name))
                for entry in it
                if entry.name.endswith(".kif") or entry.name.endswith(".kifu")
            ]
        self.problems.sort(key=lambda p: MainWindow.natural_sort_key(p.filename))
        self.curr_prob_idx = 0
        self.curr_prob = self.problems[self.curr_prob_idx]
        return
    
    def next_file(self, event=None):
        if self.curr_prob_idx+1 >= len(self.problems):
            return
        self.curr_prob = self.problems[self.curr_prob_idx + 1]
        self.curr_prob_idx += 1
        self.display_problem()
        return
    
    def prev_file(self, event=None):
        if self.curr_prob_idx-1 < 0:
            return
        self.curr_prob = self.problems[self.curr_prob_idx - 1]
        self.curr_prob_idx -= 1
        self.display_problem()
        return
    
    def open_folder(self, event=None):
        directory = filedialog.askdirectory()
        if directory == "":
            return
        self.set_directory(os.path.normpath(directory))
        for file_num, problem in enumerate(self.problems):
            self.problem_list_view.tvw.insert(
                "", "end", values=(os.path.basename(problem.filename), "-")
            )
        self.display_problem()
        return
    
    def flip_board(self, want_upside_down):
        self.board.flip_board(want_upside_down)
        return
    
    def split_timer(self):
        # what am I doing? OK kind of works but many logic issues. NEEDS WORK
        # what if last file in list? what if manually out of order?
        # also should refactor self.next_file() out of this. One function, one task.
        self.timer_controls.timer.split()
        if self.curr_prob is not None and len(self.timer_controls.timer.lap_times) != 0:
            self.curr_prob.time = self.timer_controls.timer.lap_times[-1]
            time_str = SplitTimer.sec_to_str(self.curr_prob.time)
            self.problem_list_view.set_time(self.curr_prob_idx, time_str)
            self.next_file()
        return
    
    # Speedrun mode commands
    def abort(self):
        # Abort speedrun, go back to free browsing
        return
    
    def skip(self):
        # split, mark current problem as wrong/skipped, and go next.
        self.split_timer()
        self.curr_prob.status = ProblemStatus.SKIP
        self.next_file()
        return
    
    def view_solution(self):
        # show solution, split and pause timer, change NavControl
        self.timer_controls.stop_timer()
        self.show_solution()
        self.nav_controls.show_correct_wrong()
        return
    
    def mark_correct(self):
        # mark correct, unpause timer, go to next problem, change NavControl
        self.curr_prob.status = ProblemStatus.CORRECT
        self.next_file()
        self.nav_controls.show_sol_skip()
        self.timer_controls.start_timer()
        return
    
    def mark_wrong(self):
        # mark wrong, unpause timer, go next, change NavControl
        self.curr_prob.status = ProblemStatus.WRONG
        self.next_file()
        self.nav_controls.show_sol_skip()
        self.timer_controls.start_timer()
        return
    
    @staticmethod
    def natural_sort_key(str, _nsre=re.compile(r'(\d+)')):
        return [int(c) if c.isdigit() else c.lower() for c in _nsre.split(str)]


if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root)
    root.mainloop()