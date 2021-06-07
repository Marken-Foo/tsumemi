from __future__ import annotations

import configparser
import functools
import os
import tkinter as tk

from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

import tsumemi.src.shogi.kif as kif
import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.game_controller as gamecon
import tsumemi.src.tsumemi.img_handlers as imghand
import tsumemi.src.tsumemi.problem_list as plist
import tsumemi.src.tsumemi.problem_list_controller as plistcon
import tsumemi.src.tsumemi.timer as timer
import tsumemi.src.tsumemi.timer_controller as timecon

from tsumemi.src.tsumemi.nav_controls import FreeModeNavControls, SpeedrunNavControls
from tsumemi.src.tsumemi.settings_window import SettingsWindow, CONFIG_PATH

if TYPE_CHECKING:
    from typing import List, Optional, Union
    import tsumemi.src.tsumemi.board_canvas as bc
    PathLike = Union[str, os.PathLike]


class Menubar(tk.Menu):
    """GUI class for the menubar at the top of the main window.
    """
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        
        # Set cascades
        menu_file = tk.Menu(self)
        self.add_cascade(menu=menu_file, label="File")
        menu_settings = tk.Menu(self)
        self.add_cascade(menu=menu_settings, label="Settings")
        menu_help = tk.Menu(self)
        self.add_cascade(menu=menu_help, label="Help")
        
        # File
        menu_file.add_command(
            label="Open folder...",
            command=self.controller.open_folder,
            accelerator="Ctrl+O",
            underline=0
        )
        menu_file.add_command(
            label="Open all subfolders...",
            command=self.controller.open_folder_recursive,
            accelerator="Ctrl+Shift+O",
        )
        # Settings
        menu_settings.add_command(
            label="Settings...",
            command=lambda: SettingsWindow(controller=self.controller)
        )
        # Help
        menu_help.add_command(
            label="About kif-browser",
            command=functools.partial(
                messagebox.showinfo,
                title="About kif-browser",
                message="Written in Python 3 for the shogi community. KIF files sold separately."
            )
        )
        # Bind to main window
        parent["menu"] = self
        return


def read_config_file(config: configparser.ConfigParser, filepath: PathLike
    ) -> imghand.SkinSettings:
    """Attempts to read config file; if not found, attempts to write a
    default config file.
    """
    try:
        with open(filepath, "r") as f:
            config.read_file(f)
    except FileNotFoundError:
        with open(filepath, "w+") as f:
            f.write("[skins]\n")
            f.write("pieces = TEXT\n")
            f.write("board = BROWN\n")
            f.write("komadai = WHITE\n")
        with open(filepath, "r") as f:
            config.read_file(f)
    
    skins = config["skins"]
    try:
        piece_skin = imghand.PieceSkin[skins.get("pieces")]
    except KeyError:
        piece_skin = imghand.PieceSkin.TEXT
    try:
        board_skin = imghand.BoardSkin[skins.get("board")]
    except KeyError:
        board_skin = imghand.BoardSkin.WHITE
    try:
        komadai_skin = imghand.BoardSkin[skins.get("komadai")]
    except KeyError:
        komadai_skin = imghand.BoardSkin.WHITE
    return imghand.SkinSettings(piece_skin, board_skin, komadai_skin)


class RootController(evt.IObserver):
    """Root controller for the application. Manages top-level logic
    and GUI elements.
    """
    # eventually, refactor menu labels and dialog out into a constant namespace
    def __init__(self, root: tk.Tk) -> None:
        # Program data
        self.config = configparser.ConfigParser(dict_type=dict)
        self.skin_settings = read_config_file(self.config, CONFIG_PATH)
        self.main_game = gamecon.GameController()
        self.main_timer = timecon.TimerController()
        self.main_problem_list = plistcon.ProblemListController()
        
        self.prob_buffer = self.main_problem_list.problem_list
        self.is_solution_shown: bool = False
        self.solution_text: str = ""
        
        self.main_game.add_observer(self)
        self.main_timer.clock.add_observer(self)
        self.NOTIFY_ACTIONS = {
            timer.TimerSplitEvent: self._on_split,
            gamecon.GameEndEvent: self.mark_correct_and_pause,
            gamecon.WrongMoveEvent: self.mark_wrong_and_pause,
        }
        # Everything after this point should be GUI
        # tkinter stuff, set up the main window
        self.root: tk.Tk = root
        self.root.option_add("*tearOff", False)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.title("KIF folder browser")
        
        # mainframe is the main frame of the root window
        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky="NSEW")
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.columnconfigure(1, weight=1)
        self.mainframe.rowconfigure(0, weight=1)
        
        # Make menubar
        self.menubar = Menubar(parent=self.root, controller=self)
        
        # Make canvas for board
        self.board_wrapper = ttk.Frame(self.mainframe)
        self.board_wrapper.grid(column=0, row=0, sticky="NSEW")
        self.board_wrapper.columnconfigure(0, weight=1)
        self.board_wrapper.rowconfigure(0, weight=1)
        self.board_wrapper.grid_configure(padx=5, pady=5)
        
        self.board = self.main_game.make_board_canvas(
            parent=self.board_wrapper,
            skin_settings=self.skin_settings
        )
        self.board.grid(column=0, row=0, sticky="NSEW")
        self.board.bind("<Configure>", self.board.on_resize)
        
        self.board_views: List[bc.BoardCanvas] = []
        self.board_views.append(self.board)
        
        # Initialise solution text
        self.solution = tk.StringVar(value="Open a folder of problems to display.")
        self.lbl_solution = ttk.Label(
            self.mainframe, textvariable=self.solution,
            justify="left", wraplength=self.board.width
        )
        self.lbl_solution.grid(
            column=0, row=1, sticky="W"
        )
        self.lbl_solution.grid_configure(padx=5, pady=5)
        
        # Initialise nav controls and select one to begin with
        self._navcons = {
            "free" : FreeModeNavControls(
                parent=self.mainframe, controller=self
            ),
            "speedrun" : SpeedrunNavControls(
                parent=self.mainframe, controller=self
            )
        }
        for navcon in self._navcons.values():
            navcon.grid(column=0, row=2)
            navcon.grid_remove()
        self.nav_controls = self._navcons["free"]
        self.nav_controls.grid()
        
        # Timer controls and display
        self.main_timer_view = self.main_timer.make_timer_pane(
            parent=self.mainframe
        )
        self.main_timer_view.grid(column=1, row=1)
        self.main_timer_view.columnconfigure(0, weight=0)
        self.main_timer_view.rowconfigure(0, weight=0)
        
        # Problem list
        self.problem_list_pane = self.main_problem_list.make_problem_list_pane(
            parent=self.mainframe, controller=self
        )
        self.problem_list_pane.grid(column=1, row=0, sticky="NSEW")
        self.problem_list_pane.columnconfigure(0, weight=1)
        self.problem_list_pane.rowconfigure(0, weight=1)
        self.problem_list_pane.grid_configure(padx=5, pady=5)
        
        # Keyboard shortcuts
        self.bindings = Bindings(self)
        self.bindings.bind_shortcuts(self.root, self.bindings.MASTER_SHORTCUTS)
        self.bindings.bind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return
    
    #=== Open folder, needs file open dialog
    # TODO: Refactor this into problem_list_controller.
    # After that, each "open folder" can open it either in a cliplist or
    # in a new problemlist in a self.plists: Dict (?) with the foldername?
    # as the key and/or name of the problemlist, possibly with "recursed"
    # somewhere inside.
    def open_folder(self, event: Optional[tk.Event] = None,
            recursive: bool = False
        ) -> None:
        """Prompt user for a folder, open into main_problem_list.
        """
        directory = filedialog.askdirectory()
        if directory == "":
            return
        directory = os.path.normpath(directory)
        prob = self.main_problem_list.set_directory(directory, recursive=recursive)
        if prob is not None:
            # Iff any KIF files were found, read the first and show it
            self.read_problem(prob)
            self.display_problem()
        return
    
    def open_folder_recursive(self, event: Optional[tk.Event] = None) -> None:
        return self.open_folder(event, recursive=True)
    
    def read_problem(self, prob: plist.Problem) -> None:
        filepath = prob.filepath
        if filepath is None:
            return # error out?
        game = kif.read_kif(filepath)
        if game is None:
            return # file unreadable, error out
        move_string_list = game.to_notation_ja_kif() # at end of game
        self.solution_text = "　".join(move_string_list)
        game.start()
        self.main_game.set_game(game)
        return
    
    def go_to_next_file(self, event: Optional[tk.Event] = None) -> bool:
        prob = self.prob_buffer.next()
        if prob is not None:
            self.read_problem(prob)
            self.display_problem()
            self.board.move_input_handler.enable()
            return True
        return False
    
    def go_to_prev_file(self, event: Optional[tk.Event] = None) -> bool:
        prob = self.prob_buffer.prev()
        if prob is not None:
            self.read_problem(prob)
            self.display_problem()
            self.board.move_input_handler.enable()
            return True
        return False
    
    def show_problem(self, event: Optional[tk.Event] = None, idx: int = 0
        ) -> bool:
        prob = self.main_problem_list.go_to_problem(idx)
        if prob is not None:
            self.read_problem(prob)
            self.display_problem()
            self.board.move_input_handler.enable()
            return True
        return False
    
    #=== Speedrun controller commands
    def start_speedrun(self) -> None:
        self.show_problem(idx=0)
        self.main_game.set_speedrun_mode()
        self.set_speedrun_ui()
        self.main_timer.clock.reset()
        self.main_timer.clock.start()
        return
    
    def abort_speedrun(self) -> None:
        self.main_timer.clock.stop()
        self.main_game.set_free_mode()
        self.remove_speedrun_ui()
        return
    
    def continue_speedrun(self) -> None:
        # continue speedrun from a pause, answer-checking state.
        if not self.go_to_next_file():
            self.end_of_folder()
            return
        self.nav_controls.show_sol_skip()
        self.main_timer.clock.start()
        return
    
    def end_of_folder(self) -> None:
        self.main_timer.clock.stop()
        self.show_end_of_folder_message()
        self.abort_speedrun()
        return
    
    def skip(self) -> None:
        self.split_timer()
        self.prob_buffer.set_status(plist.ProblemStatus.SKIP)
        if not self.go_to_next_file():
            self.end_of_folder()
        return
    
    def mark_correct_and_continue(self) -> None:
        self.prob_buffer.set_status(plist.ProblemStatus.CORRECT)
        self.continue_speedrun()
        return
    
    def mark_wrong_and_continue(self) -> None:
        self.prob_buffer.set_status(plist.ProblemStatus.WRONG)
        self.continue_speedrun()
        return
    
    def mark_correct_and_pause(self, event: evt.Event) -> None:
        self.prob_buffer.set_status(plist.ProblemStatus.CORRECT)
        self.split_timer()
        self.main_timer.clock.stop()
        self.show_solution()
        self.nav_controls.show_continue()
        return
    
    def mark_wrong_and_pause(self, event: evt.Event) -> None:
        self.prob_buffer.set_status(plist.ProblemStatus.WRONG)
        self.split_timer()
        self.main_timer.clock.stop()
        self.show_solution()
        self.nav_controls.show_continue()
        self.board.draw()
        return
    
    #=== GUI display methods
    def display_problem(self) -> None:
        self.board.draw()
        self.hide_solution()
        self.root.title(
            "KIF folder browser - "
            + str(self.prob_buffer.get_curr_filepath())
        )
        return
    
    def hide_solution(self) -> None:
        self.solution.set("[solution hidden]")
        self.is_solution_shown = False
        return
    
    def show_solution(self) -> None:
        self.solution.set(self.solution_text)
        self.is_solution_shown = True
        return
    
    def toggle_solution(self, event: Optional[tk.Event] = None) -> None:
        if self.is_solution_shown:
            self.hide_solution()
        else:
            self.show_solution()
        return
    
    def flip_board(self, want_upside_down: bool) -> None:
        self.board.flip_board(want_upside_down)
        return
    
    def apply_skin_settings(self, settings: imghand.SkinSettings
        ) -> None:
        self.skin_settings = settings
        piece_skin, board_skin, komadai_skin = settings.get()
        for board_canvas in self.board_views:
            board_canvas.apply_piece_skin(piece_skin)
            board_canvas.apply_board_skin(board_skin)
            board_canvas.apply_komadai_skin(komadai_skin)
            board_canvas.draw()
        return
    
    # Speedrun mode commands
    def split_timer(self) -> None:
        time = self.main_timer.clock.split()
        if time is not None:
            self.prob_buffer.set_time(time)
        return
    
    def _on_split(self, event: timer.TimerSplitEvent) -> None:
        time = event.time
        if self.main_timer.clock == event.clock and time is not None:
            self.prob_buffer.set_time(time)
        return
    
    def set_speedrun_ui(self) -> None:
        # Make UI changes
        self.nav_controls.grid_remove()
        self.nav_controls = self._navcons["speedrun"]
        self.nav_controls.show_sol_skip()
        self.nav_controls.grid()
        self.problem_list_pane.btn_speedrun.grid_remove()
        self.problem_list_pane.btn_abort_speedrun.grid()
        # Set application state
        self.bindings.unbind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return
    
    def remove_speedrun_ui(self) -> None:
        # Abort speedrun, go back to free browsing
        # Make UI changes
        self.nav_controls.grid_remove()
        self.nav_controls = self._navcons["free"]
        self.nav_controls.grid()
        self.problem_list_pane.btn_speedrun.grid()
        self.problem_list_pane.btn_abort_speedrun.grid_remove()
        # Set application state
        self.bindings.bind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return
    
    def view_solution(self) -> None:
        self.split_timer()
        self.main_timer.clock.stop()
        self.show_solution()
        self.nav_controls.show_correct_wrong()
        return
    
    def show_end_of_folder_message(self) -> None:
        messagebox.showinfo(
            title="End of folder",
            message="You have reached the end of the speedrun."
        )
        return


class Bindings:
    # Just to group all shortcut bindings together for convenience.
    def __init__(self, controller):
        self.controller = controller
    
        self.MASTER_SHORTCUTS = {
            "<Control-o>": self.controller.open_folder,
            "<Control-O>": self.controller.open_folder,
            "<Control-Shift-O>": self.controller.open_folder_recursive,
            "<Control-Shift-o>": self.controller.open_folder_recursive
        }
        
        self.FREE_SHORTCUTS = {
            "<Key-h>": self.controller.toggle_solution,
            "<Key-H>": self.controller.toggle_solution,
            "<Left>": self.controller.go_to_prev_file,
            "<Right>": self.controller.go_to_next_file
        }
        
        self.SPEEDRUN_SHORTCUTS = {}
    
    @staticmethod
    def bind_shortcuts(target, shortcuts):
        for keypress, command in shortcuts.items():
            target.bind(keypress, command)
        return
    
    @staticmethod
    def unbind_shortcuts(target, shortcuts):
        for keypress in shortcuts.keys():
            target.unbind(keypress)
        return


def run():
    def apply_theme_fix():
        # Fix from pyIDM on GitHub:
        # https://github.com/pyIDM/PyIDM/issues/128#issuecomment-655477524
        # fix for table colors in tkinter 8.6.9,
        # call style.map twice to work properly
        style = ttk.Style()
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option)
                    if elm[:2] != ("!disabled", "!selected")]
        style.map('Treeview', foreground=fixed_map("foreground"),
                  background=fixed_map("background"))
        style.map('Treeview', foreground=fixed_map("foreground"),
                  background=fixed_map("background"))

    root = tk.Tk()
    root_controller = RootController(root)
    apply_theme_fix()
    root.minsize(width=400, height=200) # stopgap vs canvas overshrinking bug
    root.mainloop()