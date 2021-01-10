from collections import Counter
import os
import tkinter as tk
from tkinter import ttk, font, filedialog

import kif_parser


class MainWindow:
    # Class encapsulating the window to display the kif.
    
    # member variables that deal with the file system
    directory = None
    kif_files = []
    current_file = None
    # other member variables
    kif_reader = kif_parser.TsumeKifReader()
    is_solution_shown = False
    
    #TODO: clean up this class and see if it can be refactored.
    def __init__(self):
        # tkinter stuff, set up the main window
        self.root = tk.Tk()
        self.root.title("KIF folder browser")
        self.root.option_add("*tearOff", False)
        
        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky="NSEW")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # make menubar
        menubar = tk.Menu(self.root)
        menu_file = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_file, label="File")
        menu_file.add_command(label="Open folder...", command=self.open_folder, accelerator="Ctrl+O")
        self.root["menu"] = menubar
        
        # Create canvas for board, determine the available drawing area
        self.boardWrapper = tk.Frame(self.mainframe)
        self.boardWrapper.grid(column=0, row=0, columnspan=3, sticky="NSEW")
        self.canvas = tk.Canvas(self.boardWrapper, width=530, height=440, bg="white")
        self.canvas.grid(column=0, row=0, sticky="NSEW")
        
        # initialise solution text
        self.solution = tk.StringVar(value="Open a folder of problems to display.")
        ttk.Label(self.mainframe, textvariable=self.solution).grid(column=0, row=1, columnspan=3, sticky="W")
        
        # Buttons to navigate and show/hide solution
        ttk.Button(self.mainframe, text="< Prev", command=self.prev_file).grid(column=0, row=2, sticky="ES")
        self.btn_show_hide = ttk.Button(self.mainframe, text="Show/hide solution", command=self.toggle_solution).grid(column=1, row=2, sticky="S")
        ttk.Button(self.mainframe, text="Next >", command=self.next_file).grid(column=2, row=2, sticky="SW")
        
        # keyboard shortcuts
        self.root.bind("<Key-h>", self.toggle_solution)
        self.root.bind("<Left>", self.prev_file)
        self.root.bind("<Right>", self.next_file)
        self.root.bind("<Control_L><Key-o>", self.open_folder)
        
        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)
        
        # make some elements scalable with window size
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.columnconfigure(1, weight=1)
        self.mainframe.columnconfigure(2, weight=1)
        self.mainframe.rowconfigure(0, weight=1)
        self.boardWrapper.columnconfigure(0, weight=1)
        self.boardWrapper.rowconfigure(0, weight=1)
        
        self.root.mainloop()
        return
        
    def draw_board(self):
        sq_w = 44
        sq_h = 48
        w_pad = 3
        h_pad = 4
        komadai_w = sq_w*1.5
        def x_sq(i):
            return w_pad + komadai_w + sq_w * i
        def y_sq(j):
            return h_pad + sq_h * j
        
        # draw board
        for i in range(10):
            self.canvas.create_line(x_sq(i), y_sq(0), x_sq(i), y_sq(9), fill="black", width=2)
            self.canvas.create_line(x_sq(0), y_sq(i), x_sq(9), y_sq(i), fill="black", width=2)
        # draw board pieces
        for row_num, row in enumerate(self.kif_reader.board.sente):
            for col_num, piece in enumerate(row):
                self.canvas.create_text(x_sq(col_num+0.5), y_sq(row_num+0.5), text=str(piece), font=(font.nametofont("TkDefaultFont"), int(sq_w/2)))
                
        for row_num, row in enumerate(self.kif_reader.board.gote):
            for col_num, piece in enumerate(row):
                self.canvas.create_text(x_sq(col_num+0.5), y_sq(row_num+0.5), text=str(piece), font=(font.nametofont("TkDefaultFont"), int(sq_w/2)), angle=180)
        # draw sente hand pieces
        sente_hand = []
        c = Counter(self.kif_reader.board.sente_hand)
        for piece in c:
            sente_hand.append(str(piece) + str(c[piece]))
        if len(sente_hand) == 0:
            sente_hand.append("な\nし")
        self.canvas.create_text(x_sq(9.7), y_sq(8), text="\n".join(sente_hand), font=(font.nametofont("TkDefaultFont"), int(sq_w*2/5)))
        return
        
    def display_problem(self):
        # parses current_file and draws problem to canvas.
        encodings = ["cp932", "utf-8"]
        for e in encodings:
            try:
                with open(self.current_file, "r", encoding=e) as kif:
                    self.kif_reader.parse_kif(kif)
            except UnicodeDecodeError:
                pass
            else:
                break
        self.canvas.delete("all")
        self.draw_board()
        self.hide_solution()
        self.root.title("KIF folder browser - " + str(self.current_file))
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
        # updates filesystem-related variables, does not update kif reader.
        self.directory = directory
        self.kif_files = [os.path.join(self.directory, filename) for filename in os.listdir(self.directory) if filename.endswith(".kif") or filename.endswith(".kifu")]
        self.current_file = self.kif_files[0]
        return
    
    def next_file(self, event=None):
        current_idx = self.kif_files.index(self.current_file)
        if current_idx + 1 >= len(self.kif_files):
            return
        self.current_file = self.kif_files[current_idx + 1]
        self.display_problem()
        return
    
    def prev_file(self, event=None):
        current_idx = self.kif_files.index(self.current_file)
        if current_idx - 1 < 0:
            return
        self.current_file = self.kif_files[current_idx - 1]
        self.display_problem()
        return
    
    def open_folder(self, event=None):
        self.set_directory(filedialog.askdirectory())
        self.display_problem()
        return


if __name__ == "__main__":
    MainWindow()