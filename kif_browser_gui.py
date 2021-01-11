from collections import Counter
import os
import re
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
    
    #TODO: clean up this class and see if some parts can be refactored out.
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
        menu_file.add_command(label="Open folder...", command=self.open_folder,
                              accelerator="Ctrl+O")
        self.root["menu"] = menubar
        
        # Create canvas for board, determine the available drawing area
        self.boardWrapper = tk.Frame(self.mainframe)
        self.boardWrapper.grid(column=0, row=0, columnspan=3, sticky="NSEW")
        self.canvas_width = 530
        self.canvas_height = 440
        self.canvas = tk.Canvas(self.boardWrapper, width=self.canvas_width,
                                height=self.canvas_height,
                                bg="white")
        self.canvas.grid(column=0, row=0, sticky="NSEW")
        self.canvas.bind("<Configure>", self.on_resize)
        
        # initialise solution text
        self.solution = tk.StringVar(value="Open a folder of problems to display.")
        ttk.Label(
            self.mainframe, textvariable=self.solution
        ).grid(
            column=0, row=1, columnspan=3, sticky="W"
        )
        
        # Buttons to navigate and show/hide solution
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
        
        # keyboard shortcuts
        self.root.bind("<Key-h>", self.toggle_solution)
        self.root.bind("<Left>", self.prev_file)
        self.root.bind("<Right>", self.next_file)
        self.root.bind("<Control_L><Key-o>", self.open_folder)
        self.root.bind("<Control_R><Key-o>", self.open_folder)
        
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
        
    def on_resize(self, event):
        self.canvas_width = event.width
        self.canvas_height = event.height
        # redraw board, passing it the new parameters
        self.canvas.delete("all")
        self.draw_board()
    
    def draw_board(self):
        # calculate the appropriate dimensions from the width and height given
        # 9x9 board, 1.5*[square width] komadai, so 12*sq_w and 9*sq_h needed
        sq_aspect_ratio = 11 / 12
        komadai_ratio = 1.5
        w_pad = 3
        h_pad = 4
        
        max_sq_w = (self.canvas_width - 2 * w_pad) / (9 + 2 * komadai_ratio)
        max_sq_h = (self.canvas_height - 2 * h_pad) / 9
        
        sq_w = min(max_sq_w, max_sq_h * sq_aspect_ratio)
        sq_h = sq_w / sq_aspect_ratio
        komadai_w = sq_w * komadai_ratio
        sq_text_size = int(sq_w / 2)
        komadai_text_size = int(sq_w * 2 / 5)
        
        def x_sq(i):
            return w_pad + komadai_w + sq_w * i
        def y_sq(j):
            return h_pad + sq_h * j
        
        # draw board
        for i in range(10):
            self.canvas.create_line(x_sq(i), y_sq(0), x_sq(i), y_sq(9),
                                    fill="black", width=2)
            self.canvas.create_line(x_sq(0), y_sq(i), x_sq(9), y_sq(i),
                                    fill="black", width=2)
        # draw board pieces
        for row_num, row in enumerate(self.kif_reader.board.sente):
            for col_num, piece in enumerate(row):
                self.canvas.create_text(
                    x_sq(col_num+0.5), y_sq(row_num+0.5), text=str(piece),
                    font=(font.nametofont("TkDefaultFont"), sq_text_size)
                )
                
        for row_num, row in enumerate(self.kif_reader.board.gote):
            for col_num, piece in enumerate(row):
                self.canvas.create_text(
                    x_sq(col_num+0.5), y_sq(row_num+0.5), text=str(piece),
                    font=(font.nametofont("TkDefaultFont"), sq_text_size),
                    angle=180
                )
        # draw sente hand pieces
        sente_hand = ["▲\n持\n駒\n"]
        c = Counter(self.kif_reader.board.sente_hand)
        for piece in c:
            sente_hand.append(str(piece) + str(c[piece]))
        if len(sente_hand) == 1:
            sente_hand.append("な\nし")
        self.canvas.create_text(
            x_sq(9) + komadai_w, y_sq(9), text="\n".join(sente_hand),
            font=(font.nametofont("TkDefaultFont"), komadai_text_size), anchor="se"
        )
        # draw gote hand pieces
        gote_hand = ["△\n持\n駒\n"]
        c = Counter(self.kif_reader.board.gote_hand)
        for piece in c:
            gote_hand.append(str(piece) + str(c[piece]))
        if len(gote_hand) == 1:
            gote_hand.append("な\nし")
        self.canvas.create_text(
            w_pad, h_pad, text="\n".join(gote_hand),
            font=(font.nametofont("TkDefaultFont"), komadai_text_size), anchor="nw"
        )
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
        self.set_directory(os.path.normpath(filedialog.askdirectory()))
        self.display_problem()
        return
    
    @staticmethod
    def natural_sort(it):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split(r'(\d+)', key)]
        return it.sort(key=alphanum_key)


if __name__ == "__main__":
    MainWindow()