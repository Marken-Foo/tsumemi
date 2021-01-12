from collections import Counter
import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, font, messagebox

import kif_parser


class MainWindow:
    '''Class encapsulating the window to display the kif.'''
    # Member variables that deal with the file system
    directory = None
    kif_files = []
    current_file = None
    # Current canvas size for board
    canvas_width = 570
    canvas_height = 460
    # Other member variables
    kif_reader = kif_parser.TsumeKifReader()
    is_solution_shown = False
    
    # eventually, refactor menu labels and dialog out into a consant namespace
    def __init__(self):
        # tkinter stuff, set up the main window
        self.root = tk.Tk()
        self.root.title("KIF folder browser")
        self.root.option_add("*tearOff", False)
        
        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky="NSEW")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Make menubar
        menubar = tk.Menu(self.root)
        menu_file = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_file, label="File")
        menu_file.add_command(label="Open folder...", command=self.open_folder,
                              accelerator="Ctrl+O", underline=0)
        self.root["menu"] = menubar
        
        menu_help = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_help, label="Help")
        
        #menu_help.add_command(label="Help", command=None)
        menu_help.add_command(label="About kif-browser", command=lambda: messagebox.showinfo(title="About kif-browser", message="Written in Python 3 for the shogi community. KIF files sold separately."))
        
        # Make canvas for board
        self.boardWrapper = tk.Frame(self.mainframe)
        self.boardWrapper.grid(column=0, row=0, columnspan=3, sticky="NSEW")
        self.canvas = tk.Canvas(self.boardWrapper, width=self.canvas_width,
                                height=self.canvas_height,
                                bg="white")
        self.canvas.grid(column=0, row=0, sticky="NSEW")
        self.canvas.bind("<Configure>", self.on_resize)
        
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
        # Keyboard shortcuts
        self.root.bind("<Key-h>", self.toggle_solution)
        self.root.bind("<Left>", self.prev_file)
        self.root.bind("<Right>", self.next_file)
        self.root.bind("<Control_L><Key-o>", self.open_folder)
        self.root.bind("<Control_R><Key-o>", self.open_folder)
        
        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)
        
        # Make some elements scalable with window size
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
        # Redraw board after setting new dimensions
        self.canvas.delete("all")
        self.draw_board()
        return
    
    # can refactor and pass the Canvas as an argument to separate dependencies?
    # or wrap canvas and put this method in the wrapper class
    def draw_board(self):
        # First calculate appropriate dimensions from self.width and height.
        # Constant proportions:
        SQ_ASPECT_RATIO = 11 / 12
        KOMADAI_W_IN_SQ = 1.5
        INNER_H_PAD = 30
        # Geometry: 9x9 shogi board, flanked by komadai area on either side
        max_sq_w = self.canvas_width / (9 + 2*KOMADAI_W_IN_SQ)
        max_sq_h = (self.canvas_height - 2*INNER_H_PAD) / 9
        # Determine whether the width or the height is the limiting factor
        sq_w = min(max_sq_w, max_sq_h*SQ_ASPECT_RATIO)
        # Propagate other measurements
        sq_h = sq_w / SQ_ASPECT_RATIO
        komadai_w = sq_w * KOMADAI_W_IN_SQ
        if sq_w == max_sq_w:
            w_pad = 0
            h_pad = INNER_H_PAD + (self.canvas_height - 9*sq_h) / 2
        else:
            w_pad = (self.canvas_width - 2*komadai_w - 9*sq_w) / 2
            h_pad = INNER_H_PAD
        sq_text_size = int(sq_w / 2)
        komadai_text_size = int(sq_w * 2/5)
        coords_text_size = int(sq_w * 2/9)
        def x_sq(i):
            return w_pad + komadai_w + sq_w * i
        def y_sq(j):
            return h_pad + sq_h * j
        
        # Draw board
        for i in range(10):
            self.canvas.create_line(x_sq(i), y_sq(0), x_sq(i), y_sq(9),
                                    fill="black", width=2)
            self.canvas.create_line(x_sq(0), y_sq(i), x_sq(9), y_sq(i),
                                    fill="black", width=2)
        # Draw board pieces
        for row_num, row in enumerate(self.kif_reader.board.sente):
            for col_num, piece in enumerate(row):
                self.canvas.create_text(
                    x_sq(col_num+0.5), y_sq(row_num+0.5),
                    text=str(piece),
                    font=(font.nametofont("TkDefaultFont"), sq_text_size)
                )
        for row_num, row in enumerate(self.kif_reader.board.gote):
            for col_num, piece in enumerate(row):
                self.canvas.create_text(
                    x_sq(col_num+0.5), y_sq(row_num+0.5),
                    text=str(piece),
                    font=(font.nametofont("TkDefaultFont"), sq_text_size),
                    angle=180
                )
        # Draw board coordinates
        for row_num in range(1, 10, 1):
            self.canvas.create_text(
                x_sq(9), y_sq(row_num-1+0.5),
                text=" " + kif_parser.KanjiNumber(row_num).name,
                font=(font.nametofont("TkDefaultFont"), coords_text_size),
                anchor="w"
            )
        for col_num in range(9, 0, -1):
            self.canvas.create_text(
                x_sq(9-col_num+0.5), y_sq(0),
                text=str(col_num),
                font=(font.nametofont("TkDefaultFont"), coords_text_size),
                anchor="s"
            )
        # Draw sente hand pieces
        sente_hand = ["▲\n持\n駒\n"]
        c = Counter(self.kif_reader.board.sente_hand)
        for piece in c:
            sente_hand.append(str(piece) + str(c[piece]))
        if len(sente_hand) == 1:
            sente_hand.append("な\nし")
        self.canvas.create_text(
            x_sq(9) + komadai_w, y_sq(9),
            text="\n".join(sente_hand),
            font=(font.nametofont("TkDefaultFont"), komadai_text_size),
            anchor="se"
        )
        # Draw gote hand pieces
        gote_hand = ["△\n持\n駒\n"]
        c = Counter(self.kif_reader.board.gote_hand)
        for piece in c:
            gote_hand.append(str(piece) + str(c[piece]))
        if len(gote_hand) == 1:
            gote_hand.append("な\nし")
        self.canvas.create_text(
            w_pad, h_pad,
            text="\n".join(gote_hand),
            font=(font.nametofont("TkDefaultFont"), komadai_text_size),
            anchor="nw"
        )
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
    
    @staticmethod
    def natural_sort(it):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split(r'(\d+)', key)]
        return it.sort(key=alphanum_key)


if __name__ == "__main__":
    MainWindow()