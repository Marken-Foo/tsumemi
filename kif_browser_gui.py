import os
import tkinter as tk

from tkinter import filedialog, messagebox, ttk

import model

from board_canvas import BoardCanvas
from model import Model, ProblemStatus
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
        
        parent["menu"] = self
        return


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


class TimerPane(ttk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        
        # Basic timer
        self.timer = SplitTimer()
        # The Label will update itself via Observer pattern when refactored.
        self.timer_display_str = tk.StringVar(value=SplitTimer.sec_to_str(0.0))
        self.timer_display = ttk.Label(
            self, textvariable=self.timer_display_str
        )
        self.timer_display.grid(
            column=0, row=0, columnspan=3
        )
        # Format timer appearance
        self.timer_display.configure(
            background="black",
            foreground="light sky blue",
            font=("TkDefaultFont", 48)
        )
        # Timer control widgets
        ttk.Button(
            self, text="Start/stop timer",
            command=self.toggle_timer
        ).grid(
            column=0, row=1
        )
        ttk.Button(
            self, text="Reset timer",
            command=self.reset
        ).grid(
            column=1, row=1
        )
        ttk.Button(
            self, text="Split",
            command=self.controller.split_timer
        ).grid(
            column=2, row=1
        )
    
    def start(self):
        self.timer.start()
        self.refresh_timer()
        return
        
    def stop(self):
        self.timer.stop()
        return
    
    def toggle_timer(self):
        if self.timer.is_running:
            self.stop()
        else:
            self.start()
        return
    
    def reset(self):
        self.timer.stop()
        self.timer.reset()
        self.refresh_timer()
        return
    
    def refresh_timer(self):
        self.timer_display_str.set(SplitTimer.sec_to_str(self.timer.read()))
        if self.timer.is_running:
            self.timer_display.after(40, self.refresh_timer)
        return


class ProblemsView(ttk.Treeview):
    '''
    Displays list of problems in currently open folder.
    As it is a view of the underlying data model, it uses the Observer pattern
    to update itself whenever the model updates.
    '''
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        
        self.notify_actions = {
            model.ProbStatusEvent: self.set_status,
            model.ProbTimeEvent: self.set_time,
            model.ProbDirEvent: self.refresh_view
        }
        self.status_strings = {
            ProblemStatus.SKIP: "-",
            ProblemStatus.CORRECT: "O",
            ProblemStatus.WRONG: "X"
        }
        
        self["columns"] = ("filename", "time", "status")
        self["show"] = "headings"
        self.heading("filename", text="Problem")
        self.heading("time", text="Time")
        self.column("time", width=120)
        self.heading("status", text="Status")
        self.column("status", anchor="center", width=40)
        # Colours to be decided (accessibility)
        self.tag_configure("SKIP", background="snow2")
        self.tag_configure("CORRECT", background="PaleGreen1")
        self.tag_configure("WRONG", background="LightPink1")
        return
    
    def set_time(self, event):
        idx = event.idx
        time = event.time
        # Set time column for item at given index
        id = self.get_children()[idx]
        time_str = SplitTimer.sec_to_str(time)
        self.set(id, column="time", value=time_str)
        return
    
    def set_status(self, event):
        idx = event.idx
        status = event.status
        id = self.get_children()[idx]
        self.set(id, column="status", value=self.status_strings[status])
        curr_tags = self.item(id)["tags"]
        # tags returns empty string (!) if none, or list of str if at least one
        if not curr_tags:
            curr_tags = [status.name]
            self.item(id, tags=curr_tags)
        elif status.name not in curr_tags:
            curr_tags.append(status.name)
            self.item(id, tags=curr_tags)
        else:
            pass # no need to update item
        return
    
    def refresh_view(self, event):
        # Refresh the entire view as the model changed, e.g. on opening folder
        problems = event.prob_list
        self.delete(*self.get_children())
        for problem in problems:
            filename = os.path.basename(problem.filename)
            time_str = "-" if problem.time is None \
                       else SplitTimer.sec_to_str(problem.time)
            self.insert(
                "", "end", values=(filename, time_str)
            )
        return
    
    def get_selection_idx(self, event):
        return self.index(self.selection()[0])
    
    def on_notify(self, event):
        # Observer pattern
        self.notify_actions[type(event)](event)
        return


class ProblemListPane(ttk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        
        # Display problem list as Treeview
        self.tvw = ProblemsView(parent=self, controller=controller)
        self.tvw.grid(column=0, row=0, sticky="NSEW")
        
        # Make scrollbar
        self.scrollbar_tvw = ttk.Scrollbar(
            self, orient="vertical",
            command=self.tvw.yview
        )
        self.scrollbar_tvw.grid(column=1, row=0, sticky="NS")
        self.tvw["yscrollcommand"] = self.scrollbar_tvw.set
        
        # Make speedrun mode button
        self.btn_speedrun = ttk.Button(self, text="Start speedrun", command=controller.start_speedrun)
        self.btn_speedrun.grid(column=0, row=1)
        self.btn_speedrun.grid_remove()
        self.btn_abort_speedrun = ttk.Button(self, text="Abort speedrun", command=controller.abort)
        self.btn_abort_speedrun.grid(column=0, row=1)
        self.btn_abort_speedrun.grid_remove()
        
        self.btn_speedrun.grid()


class MainWindow:
    '''Class encapsulating the window to display the kif.'''
    # eventually, refactor menu labels and dialog out into a constant namespace
    def __init__(self, master):
        # Set up data model
        self.model = Model(self)
        # tkinter stuff, set up the main window
        # Reference to tk.Tk() root object
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
        self.boardWrapper.grid_configure(padx=5, pady=5)
        
        self.board = BoardCanvas(
            parent=self.boardWrapper, controller=self,
            width=BoardCanvas.canvas_width, height=BoardCanvas.canvas_height,
            bg="white"
        )
        self.board.grid(column=0, row=0, sticky="NSEW")
        self.board.bind("<Configure>", self.board.on_resize)
        
        # Initialise solution text
        self.is_solution_shown = False
        self.solution = tk.StringVar(value="Open a folder of problems to display.")
        self.lbl_solution = ttk.Label(
            self.mainframe, textvariable=self.solution,
            justify="left", wraplength=self.board.canvas_width
        )
        self.lbl_solution.grid(
            column=0, row=1, sticky="W"
        )
        self.lbl_solution.grid_configure(padx=5, pady=5)
        
        # Initialise nav controls and select one to begin with
        self._navcons = {
            "free" : FreeModeNavControls(parent=self.mainframe, controller=self),
            "speedrun" : SpeedrunNavControls(parent=self.mainframe, controller=self)
        }
        for navcon in self._navcons.values():
            navcon.grid(column=0, row=2)
            navcon.grid_remove()
        self.nav_controls = self._navcons["free"]
        self.nav_controls.grid()
        
        # Timer controls and display
        self.timer_controls = TimerPane(parent=self.mainframe, controller=self)
        self.timer_controls.grid(column=1, row=1)
        self.timer_controls.columnconfigure(0, weight=0)
        self.timer_controls.rowconfigure(0, weight=0)
        
        # Problem list
        self.problem_list_pane = ProblemListPane(parent=self.mainframe, controller=self)
        self.problem_list_pane.grid(column=1, row=0)
        self.problem_list_pane.grid_configure(padx=5, pady=5)
        # Observer pattern; treeview updates itself when model updates
        tvw = self.problem_list_pane.tvw
        self.model.add_observer(tvw)
        # Double click to go to problem
        tvw.bind("<Double-1>", lambda e: self.go_to_file(idx=tvw.get_selection_idx(e)))
        
        # Keyboard shortcuts
        self.master.bind("<Key-h>", self.toggle_solution)
        self.master.bind("<Left>", self.prev_file)
        self.master.bind("<Right>", self.next_file)
        self.master.bind("<Control_L><Key-o>", self.open_folder)
        self.master.bind("<Control_R><Key-o>", self.open_folder)
        return
        
    def display_problem(self):
        self.board.draw()
        self.hide_solution()
        self.master.title("KIF folder browser - " + str(self.model.curr_prob.filename))
        return
    
    def hide_solution(self):
        self.solution.set("[solution hidden]")
        self.is_solution_shown = False
        return
    
    def show_solution(self):
        self.solution.set(self.model.solution)
        self.is_solution_shown = True
        return
    
    def toggle_solution(self, event=None):
        if self.is_solution_shown:
            self.hide_solution()
        else:
            self.show_solution()
        return
    
    def next_file(self, event=None):
        res = self.model.open_next_file()
        if res:
            self.display_problem()
        return res
    
    def prev_file(self, event=None):
        res = self.model.open_prev_file()
        if res:
            self.display_problem()
        return res
    
    def go_to_file(self, idx, event=None):
        res = self.model.open_file(idx)
        if res:
            self.display_problem()
        return res
    
    def open_folder(self, event=None):
        directory = filedialog.askdirectory()
        if directory == "":
            return
        self.model.set_directory(os.path.normpath(directory))
        self.display_problem()
        return
    
    def flip_board(self, want_upside_down):
        self.board.flip_board(want_upside_down)
        return
    
    def split_timer(self):
        # what am I doing? OK kind of works but many logic issues. NEEDS WORK
        # what if last file in list? what if manually out of order?
        self.timer_controls.timer.split()
        if self.model.curr_prob is not None and len(self.timer_controls.timer.lap_times) != 0:
            time = self.timer_controls.timer.lap_times[-1]
            self.model.set_time(time)
        return
    
    # Speedrun mode commands
    def start_speedrun(self):
        # Make UI changes
        self.nav_controls.grid_remove()
        self.nav_controls = self._navcons["speedrun"]
        self.nav_controls.show_sol_skip()
        self.nav_controls.grid()
        self.problem_list_pane.btn_speedrun.grid_remove()
        self.problem_list_pane.btn_abort_speedrun.grid()
        
        # Unbind keyboard shortcuts
        self.master.unbind("<Key-h>")
        self.master.unbind("<Left>")
        self.master.unbind("<Right>")
        
        # Set application state
        self.go_to_file(idx=0)
        self.timer_controls.reset()
        self.timer_controls.start()
        return
        
    def abort(self):
        # Abort speedrun, go back to free browsing
        # Make UI changes
        self.nav_controls.grid_remove()
        self.nav_controls = self._navcons["free"]
        self.nav_controls.grid()
        self.problem_list_pane.btn_speedrun.grid()
        self.problem_list_pane.btn_abort_speedrun.grid_remove()
        
        # Rebind keyboard shortcuts
        self.master.bind("<Key-h>", self.toggle_solution)
        self.master.bind("<Left>", self.prev_file)
        self.master.bind("<Right>", self.next_file)
        
        self.timer_controls.stop()
        return
    
    def skip(self):
        # split, mark current problem as wrong/skipped, and go next.
        self.split_timer()
        self.model.set_skip()
        if not self.next_file():
            self.end_of_folder()
        return
    
    def view_solution(self):
        # show solution, split and pause timer, change NavControl
        self.split_timer()
        self.timer_controls.stop()
        self.show_solution()
        self.nav_controls.show_correct_wrong()
        return
    
    def mark_correct(self):
        # mark correct, unpause timer, go to next problem, change NavControl
        self.model.set_correct()
        if not self.next_file():
            self.end_of_folder()
            return
        self.nav_controls.show_sol_skip()
        self.timer_controls.start()
        return
    
    def mark_wrong(self):
        # mark wrong, unpause timer, go next, change NavControl
        self.model.set_wrong()
        if not self.next_file():
            self.end_of_folder()
            return
        self.nav_controls.show_sol_skip()
        self.timer_controls.start()
        return
    
    def end_of_folder(self):
        self.timer_controls.stop()
        messagebox.showinfo(
            title="End of folder",
            message="You have reached the end of the speedrun."
        )
        self.abort()
        return


if __name__ == "__main__":
    def apply_theme_fix():
        # Fix from pyIDM on GitHub:
        # https://github.com/pyIDM/PyIDM/issues/128#issuecomment-655477524
        # fix for table colors in tkinter 8.6.9, call style.map twice to work properly
        style = ttk.Style()
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option)
                    if elm[:2] != ("!disabled", "!selected")]
        style.map('Treeview', foreground=fixed_map("foreground"),
                  background=fixed_map("background"))
        style.map('Treeview', foreground=fixed_map("foreground"),
                  background=fixed_map("background"))

    root = tk.Tk()
    main_window = MainWindow(root)
    apply_theme_fix()
    root.mainloop()