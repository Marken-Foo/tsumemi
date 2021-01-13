import os
import re
import tkinter as tk

from tkinter import filedialog, messagebox, ttk

import kif_parser
from board_canvas import BoardCanvas
from split_timer import SplitTimer


class MainWindow:
    '''Class encapsulating the window to display the kif.'''
    # Reference to tk.Tk() root object
    master = None
    # Member variables that deal with the file system
    directory = None
    kif_files = []
    current_file = None
    # Other member variables
    kif_reader = kif_parser.TsumeKifReader()
    is_solution_shown = False
    
    # eventually, refactor menu labels and dialog out into a consant namespace
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
        menubar = tk.Menu(self.master)
        menu_file = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_file, label="File")
        menu_file.add_command(label="Open folder...", command=self.open_folder,
                              accelerator="Ctrl+O", underline=0)
        self.master["menu"] = menubar
        
        menu_help = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_help, label="Help")
        
        #menu_help.add_command(label="Help", command=None)
        menu_help.add_command(label="About kif-browser", command=lambda: messagebox.showinfo(title="About kif-browser", message="Written in Python 3 for the shogi community. KIF files sold separately."))
        
        # Make canvas for board
        self.boardWrapper = tk.Frame(self.mainframe)
        self.boardWrapper.grid(column=0, row=0, columnspan=3, sticky="NSEW")
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
            self.mainframe, textvariable=self.solution
        ).grid(
            column=0, row=1, columnspan=3, sticky="W"
        )
        # Make buttons to navigate and show/hide solution
        ttk.Button(
            self.mainframe, text="< Prev", command=self.prev_file
        ).grid(
            column=0, row=2, sticky="ES"
        )
        self.btn_show_hide = ttk.Button(
            self.mainframe, text="Show/hide solution", command=self.toggle_solution
        ).grid(
            column=1, row=2, sticky="S"
        )
        ttk.Button(
            self.mainframe, text="Next >", command=self.next_file
        ).grid(
            column=2, row=2, sticky="SW"
        )
        # Upside-down mode
        is_upside_down = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.mainframe, text="Upside-down mode",
            command=lambda: self.flip_board(is_upside_down.get()),
            variable=is_upside_down, onvalue=True, offvalue=False
        ).grid(
            column=0, row=3
        )
        # Basic timer
        self.timer = SplitTimer()
        self.str_timer = tk.StringVar(value="00:00:00")
        self.timer_display = ttk.Label(
            self.mainframe, textvariable=self.str_timer
        )
        self.timer_display.grid(
            column=0, row=4, sticky="W"
        )
        self.timer_display.after(40, self.refresh_timer)
        ttk.Button(
            self.mainframe, text="Start/stop timer",
            command=self.toggle_timer
        ).grid(
            column=1, row=4
        )
        ttk.Button(
            self.mainframe, text="Reset timer",
            command=self.reset_timer
        ).grid(
            column=2, row=4, sticky="W"
        )
        # Keyboard shortcuts
        self.master.bind("<Key-h>", self.toggle_solution)
        self.master.bind("<Left>", self.prev_file)
        self.master.bind("<Right>", self.next_file)
        self.master.bind("<Control_L><Key-o>", self.open_folder)
        self.master.bind("<Control_R><Key-o>", self.open_folder)
        
        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)
        
        return
        
    def display_problem(self):
        # Parse current_file and draw problem to canvas
        # Try any likely encodings for the KIF files
        encodings = ["cp932", "utf-8"]
        for e in encodings:
            try:
                with open(self.current_file, "r", encoding=e) as kif:
                    self.kif_reader.parse_kif(kif)
            except UnicodeDecodeError:
                pass
            else:
                break
        self.board.draw()
        self.hide_solution()
        self.master.title("KIF folder browser - " + str(self.current_file))
        return
    
    def hide_solution(self):
        self.solution.set("[solution hidden]")
        self.is_solution_shown = False
        return
    
    def toggle_solution(self, event=None):
        if self.is_solution_shown:
            self.hide_solution()
        else:
            solution = "　".join(self.kif_reader.moves)
            self.solution.set(solution)
            self.is_solution_shown = True
        return
    
    def set_directory(self, directory):
        # Update filesystem-related variables. Kif reader not updated.
        self.directory = directory
        self.kif_files = [
            os.path.join(self.directory, filename)
            for filename in os.listdir(self.directory)
            if filename.endswith(".kif") or filename.endswith(".kifu")
        ]
        MainWindow.natural_sort(self.kif_files)
        self.current_file = self.kif_files[0]
        return
    
    def next_file(self, event=None):
        current_idx = self.kif_files.index(self.current_file)
        if current_idx+1 >= len(self.kif_files):
            return
        self.current_file = self.kif_files[current_idx + 1]
        self.display_problem()
        return
    
    def prev_file(self, event=None):
        current_idx = self.kif_files.index(self.current_file)
        if current_idx-1 < 0:
            return
        self.current_file = self.kif_files[current_idx - 1]
        self.display_problem()
        return
    
    def open_folder(self, event=None):
        # Display first problem in folder as well
        self.set_directory(os.path.normpath(filedialog.askdirectory()))
        self.display_problem()
        return
    
    def flip_board(self, is_upside_down):
        if self.board.is_upside_down != is_upside_down:
            self.board.is_upside_down = is_upside_down
            self.board.draw()
        return
    
    def toggle_timer(self):
        if self.timer.is_running:
            self.timer.stop()
        else:
            self.timer.start()
        return
    
    def reset_timer(self):
        self.timer.stop()
        self.timer.reset()
        self.refresh_timer()
        return
    
    def refresh_timer(self):
        self.str_timer.set(SplitTimer.sec_to_str(self.timer.read()))
        self.timer_display.after(40, self.refresh_timer)
        return
    
    @staticmethod
    def natural_sort(it):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split(r'(\d+)', key)]
        return it.sort(key=alphanum_key)


if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root)
    root.mainloop()