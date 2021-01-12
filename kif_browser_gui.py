import os
import re
import tkinter as tk

from collections import Counter
from tkinter import ttk, filedialog, font, messagebox

import kif_parser
from split_timer import SplitTimer


class BoardCanvas(tk.Canvas):
    '''Class encapsulating the canvas where the board is drawn.'''
    # Default/current canvas size for board
    canvas_width = 570
    canvas_height = 460
    
    # Constant proportions
    SQ_ASPECT_RATIO = 11 / 12
    KOMADAI_W_IN_SQ = 1.5
    INNER_H_PAD = 30
    
    is_upside_down = False
    
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        return
    
    def draw(self):
        reader = self.controller.kif_reader
        # Clear board first - could also keep board and just redraw pieces
        self.delete("all")
        
        (sq_w, sq_h, komadai_w, w_pad, h_pad, sq_text_size,
         komadai_text_size, coords_text_size) = self.calculate_sizes()
        def x_sq(i):
            return w_pad + komadai_w + sq_w * i
        def y_sq(j):
            return h_pad + sq_h * j
        
        # Note: if is_upside_down, essentially performs a deep copy,
        # but just "passes by reference" the reader's board if not.
        if self.is_upside_down:
            north_hand = reader.board.gote_hand
            south_hand = reader.board.sente_hand
            north_board = reader.board.gote[::-1]
            south_board = reader.board.sente[::-1]
            for i, row in enumerate(north_board):
                north_board[i] = row[::-1]
            for i, row in enumerate(south_board):
                south_board[i] = row[::-1]
            north_hand_strings = ["△\n持\n駒\n"]
            south_hand_strings = ["▲\n持\n駒\n"]
            row_coords = [" " + kif_parser.KanjiNumber(i).name for i in range(9, 0, -1)]
            col_coords = [str(i) for i in range(1, 10, 1)]
        else:
            north_hand = reader.board.sente_hand
            south_hand = reader.board.gote_hand
            north_board = reader.board.sente
            south_board = reader.board.gote
            north_hand_strings = ["▲\n持\n駒\n"]
            south_hand_strings = ["△\n持\n駒\n"]
            row_coords = [" " + kif_parser.KanjiNumber(i).name for i in range(1, 10, 1)]
            col_coords = [str(i) for i in range(9, 0, -1)]
        
        # Draw board
        for i in range(10):
            self.create_line(x_sq(i), y_sq(0), x_sq(i), y_sq(9),
                                    fill="black", width=2)
            self.create_line(x_sq(0), y_sq(i), x_sq(9), y_sq(i),
                                    fill="black", width=2)
        # Draw board pieces
        for row_num, row in enumerate(north_board):
            for col_num, piece in enumerate(row):
                self.create_text(
                    x_sq(col_num+0.5), y_sq(row_num+0.5),
                    text=str(piece),
                    font=(font.nametofont("TkDefaultFont"), sq_text_size)
                )
        for row_num, row in enumerate(south_board):
            for col_num, piece in enumerate(row):
                self.create_text(
                    x_sq(col_num+0.5), y_sq(row_num+0.5),
                    text=str(piece),
                    font=(font.nametofont("TkDefaultFont"), sq_text_size),
                    angle=180
                )
        # Draw board coordinates
        for row_num in range(9):
            self.create_text(
                x_sq(9), y_sq(row_num+0.5),
                text=" " + row_coords[row_num],
                font=(font.nametofont("TkDefaultFont"), coords_text_size),
                anchor="w"
            )
        for col_num in range(9):
            self.create_text(
                x_sq(col_num+0.5), y_sq(0),
                text=col_coords[col_num],
                font=(font.nametofont("TkDefaultFont"), coords_text_size),
                anchor="s"
            )
        # Draw sente hand pieces
        c = Counter(north_hand)
        for piece in c:
            north_hand_strings.append(str(piece) + str(c[piece]))
        if len(north_hand_strings) == 1:
            north_hand_strings.append("な\nし")
        self.create_text(
            x_sq(9) + komadai_w, y_sq(9),
            text="\n".join(north_hand_strings),
            font=(font.nametofont("TkDefaultFont"), komadai_text_size),
            anchor="se"
        )
        # Draw gote hand pieces
        c = Counter(south_hand)
        for piece in c:
            south_hand_strings.append(str(piece) + str(c[piece]))
        if len(south_hand_strings) == 1:
            south_hand_strings.append("な\nし")
        self.create_text(
            w_pad, h_pad,
            text="\n".join(south_hand_strings),
            font=(font.nametofont("TkDefaultFont"), komadai_text_size),
            anchor="nw"
        )
        return
    
    def on_resize(self, event):
        self.canvas_width = event.width
        self.canvas_height = event.height
        # Redraw board after setting new dimensions
        self.draw()
        return
    
    def calculate_sizes(self):
        # Geometry: 9x9 shogi board, flanked by komadai area on either side
        max_sq_w = self.canvas_width / (9 + 2*self.KOMADAI_W_IN_SQ)
        max_sq_h = (self.canvas_height - 2*self.INNER_H_PAD) / 9
        # Determine whether the width or the height is the limiting factor
        sq_w = min(max_sq_w, max_sq_h*self.SQ_ASPECT_RATIO)
        # Propagate other measurements
        sq_h = sq_w / self.SQ_ASPECT_RATIO
        komadai_w = sq_w * self.KOMADAI_W_IN_SQ
        if sq_w == max_sq_w:
            w_pad = 0
            h_pad = self.INNER_H_PAD + (self.canvas_height - 9*sq_h) / 2
        else:
            w_pad = (self.canvas_width - 2*komadai_w - 9*sq_w) / 2
            h_pad = self.INNER_H_PAD
        sq_text_size = int(sq_w / 2)
        komadai_text_size = int(sq_w * 2/5)
        coords_text_size = int(sq_w * 2/9)
        return (sq_w, sq_h, komadai_w, w_pad, h_pad,
                sq_text_size, komadai_text_size, coords_text_size)


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
            column=0, row=4
        )
        self.timer_display.after(40, self.refresh_timer)
        ttk.Button(
            self.mainframe, text="Start/stop timer",
            command=self.toggle_timer
        ).grid(
            column=1, row=4
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