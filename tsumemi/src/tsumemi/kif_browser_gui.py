from __future__ import annotations

import configparser
import datetime
import functools
import logging.config
import os
import tkinter as tk

from tkinter import filedialog, font, messagebox, ttk
from typing import TYPE_CHECKING

import tsumemi.src.shogi.kif as kif
import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.game_controller as gamecon
import tsumemi.src.tsumemi.img_handlers as imghand
import tsumemi.src.tsumemi.problem_list as plist
import tsumemi.src.tsumemi.problem_list_controller as plistcon
import tsumemi.src.tsumemi.speedrun_controller as speedcon
import tsumemi.src.tsumemi.timer as timer
import tsumemi.src.tsumemi.timer_controller as timecon

from tsumemi.src.tsumemi.nav_controls import FreeModeNavControls, SpeedrunNavControls
from tsumemi.src.tsumemi.settings_window import SettingsWindow, CONFIG_PATH

if TYPE_CHECKING:
    from typing import List, Optional, Union
    import tsumemi.src.tsumemi.board_canvas as bc
    PathLike = Union[str, os.PathLike]


def _read_config_file(config: configparser.ConfigParser, filepath: PathLike
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
        self.skin_settings = _read_config_file(self.config, CONFIG_PATH)
        self.main_game = gamecon.GameController(self.skin_settings)
        self.main_timer = timecon.TimerController()
        self.main_problem_list = plistcon.ProblemListController()
        
        self.speedrun_controller = speedcon.SpeedrunController(self)
        
        self.main_game.add_observer(self.speedrun_controller._speedrun_states["question"])
        self.main_timer.clock.add_observer(self)
        self.main_problem_list.problem_list.add_observer(self)
        self.NOTIFY_ACTIONS = {
            timer.TimerSplitEvent: self._on_split,
            plist.ProbSelectedEvent: self._on_prob_selected,
        }
        # Everything after this point should be GUI
        self.root: tk.Tk = root
        root.option_add("*tearOff", False)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        root.title("tsumemi")
        
        self.menubar: Menubar = Menubar(parent=self.root, controller=self)
        
        mainframe = MainWindowView(root, self)
        self.mainframe = mainframe
        board_canvas = self.mainframe.add_board_frame(
            self.main_game.make_navigable_view
        )
        self.mainframe.add_timer_view(
            self.main_timer.make_timer_pane
        )
        self.mainframe.add_problem_list_pane(
            self.main_problem_list.make_problem_list_pane
        )
        self.lbl_solution = self.mainframe.add_solution_pane(
            SolutionLabel,
            height=3, justify="left", wraplength=board_canvas.width
        )
        self.mainframe.grid_items_normal()
        
        # assign all views to self for later reference if needed.
        self.board = board_canvas
        self.board_views: List[bc.BoardCanvas] = []
        self.board_views.append(board_canvas)
        
        # Keyboard shortcuts
        self.bindings = Bindings(self)
        self.bindings.bind_shortcuts(self.root, self.bindings.MASTER_SHORTCUTS)
        self.bindings.bind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return
    
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
        return
    
    def open_folder_recursive(self, event: Optional[tk.Event] = None) -> None:
        return self.open_folder(event, recursive=True)
    
    def copy_sfen_to_clipboard(self) -> None:
        sfen = self.main_game.get_current_sfen()
        self.root.clipboard_clear()
        self.root.clipboard_append(sfen)
        self.root.update()
        return
    
    def show_problem(self, prob: plist.Problem) -> None:
        """Display the given problem in the GUI and enable move input.
        """
        self._read_problem(prob)
        window_title = "tsumemi - " + str(prob.filepath)
        self.board.draw()
        move_input_handler = self.board.move_input_handler
        if move_input_handler is not None:
            move_input_handler.enable()
        self.lbl_solution.hide_solution()
        self.root.title(window_title)
        return
    
    def _read_problem(self, prob: plist.Problem) -> None:
        """Read the problem data from file into the program.
        """
        filepath = prob.filepath
        if filepath is None:
            return # error out?
        game = kif.read_kif(filepath)
        if game is None:
            return # file unreadable, error out
        move_string_list = game.to_notation_ja_kif() # at end of game
        self.lbl_solution.set_solution_text("　".join(move_string_list))
        game.go_to_start()
        self.main_game.set_game(game)
        return
    
    def go_next_file(self, event: Optional[tk.Event] = None) -> bool:
        prob = self.main_problem_list.go_next_problem()
        return prob is not None
    
    def go_prev_file(self, event: Optional[tk.Event] = None) -> bool:
        prob = self.main_problem_list.go_prev_problem()
        return prob is not None
    
    def go_to_file(self, event: Optional[tk.Event] = None, idx: int = 0
        ) -> bool:
        # GUI callback
        prob = self.main_problem_list.go_to_problem(idx)
        return prob is not None
    
    def clear_statuses(self) -> None:
        self.main_problem_list.clear_statuses()
        return
    
    def clear_times(self) -> None:
        self.main_problem_list.clear_times()
        return
    
    def clear_results(self) -> None:
        self.main_problem_list.clear_statuses()
        self.main_problem_list.clear_times()
        return
    
    def generate_statistics(self) -> None:
        stats = self.main_problem_list.generate_statistics()
        StatisticsDialog(stats)
        return
    
    def export_prob_list_csv(self) -> None:
        date_time_now = datetime.datetime.now()
        datetimestr = date_time_now.strftime("%Y%m%d-%H%M")
        directory: str = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("Comma-separated values", ".csv"),),
            initialfile=f"tsume-speedrun-{datetimestr}",
        )
        if directory == "":
            return
        self.main_problem_list.export_as_csv(directory)
        return
    
    #=== Speedrun controller commands
    def start_speedrun(self) -> None:
        self.speedrun_controller.start_speedrun()
        return
    
    def abort_speedrun(self) -> None:
        self.speedrun_controller.abort_speedrun()
        return
    
    def set_speedrun_ui(self) -> None:
        # Make UI changes
        self.mainframe.nav_controls.grid_remove()
        self.mainframe.nav_controls = self.mainframe._navcons["speedrun"]
        self.mainframe.nav_controls.show_sol_skip()
        self.mainframe.nav_controls.grid()
        # Set application state
        self.bindings.unbind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return
    
    def remove_speedrun_ui(self) -> None:
        # Abort speedrun, go back to free browsing
        # Make UI changes
        self.mainframe.nav_controls.grid_remove()
        self.mainframe.nav_controls = self.mainframe._navcons["free"]
        self.mainframe.nav_controls.grid()
        # Set application state
        self.bindings.bind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return
    
    #=== GUI display methods
    def toggle_solution(self, event: Optional[tk.Event] = None) -> None:
        # GUI callback
        self.lbl_solution.toggle_solution()
        return
    
    def flip_board(self, want_upside_down: bool) -> None:
        # GUI callback
        self.board.flip_board(want_upside_down)
        return
    
    def apply_skin_settings(self, settings: imghand.SkinSettings
        ) -> None:
        # GUI callback
        self.skin_settings = settings
        self.main_game.skin_settings = settings
        piece_skin, board_skin, komadai_skin = settings.get()
        for board_canvas in self.board_views:
            board_canvas.apply_piece_skin(piece_skin)
            board_canvas.apply_board_skin(board_skin)
            board_canvas.apply_komadai_skin(komadai_skin)
            board_canvas.draw()
        return
    
    #=== Observer callbacks
    def _on_split(self, event: timer.TimerSplitEvent) -> None:
        # Observer callback
        time = event.time
        if self.main_timer.clock == event.clock:
            self.main_problem_list.set_time(time)
        return
    
    def _on_prob_selected(self, event: plist.ProbSelectedEvent) -> None:
        # Observer callback
        if event.sender == self.main_problem_list.problem_list:
            self.show_problem(event.problem)
        return


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
    
    def add_board_frame(self, constructor, *args, **kwargs) -> bc.BoardCanvas:
        self.board_frame, self.board_canvas = constructor(parent=self, *args, **kwargs)
        return self.board_canvas
    
    def add_timer_view(self, constructor, *args, **kwargs) -> None:
        self.main_timer_view = constructor(parent=self, *args, **kwargs)
        return
    
    def add_problem_list_pane(self, constructor, *args, **kwargs) -> None:
        self.problem_list_pane = constructor(parent=self, *args, **kwargs)
        return
    
    def add_solution_pane(self, constructor, *args, **kwargs) -> SolutionLabel:
        self.lbl_solution = constructor(parent=self, *args, **kwargs)
        return self.lbl_solution
    
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


class SolutionLabel(tk.Label):
    """Label to display, show, and hide problem solutions.
    """
    def __init__(self, parent: tk.Widget, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.is_solution_shown: bool = True
        self.solution_text: str = "Open a folder of problems to display."
        self.textvar: tk.StringVar = tk.StringVar(value=self.solution_text)
        self["textvariable"] = self.textvar
        
        defaultfont = font.Font(font=self["font"])
        typeface = defaultfont["family"]
        fontsize = defaultfont["size"]
        self.config(font=(typeface, fontsize+2))
        return
    
    def set_solution_text(self, text: str) -> None:
        self.solution_text = text
        return
    
    def hide_solution(self) -> None:
        self.textvar.set("[solution hidden]")
        self.is_solution_shown = False
        return
    
    def show_solution(self) -> None:
        self.textvar.set(self.solution_text)
        self.is_solution_shown = True
        return
    
    def toggle_solution(self, event: Optional[tk.Event] = None) -> None:
        if self.is_solution_shown:
            self.hide_solution()
        else:
            self.show_solution()
        return


class Bindings:
    # Just to group all shortcut bindings together for convenience.
    def __init__(self, controller):
        self.controller = controller
    
        self.MASTER_SHORTCUTS = {
            "<Control-o>": self.controller.open_folder,
            "<Control-O>": self.controller.open_folder,
            "<Control-Shift-O>": self.controller.open_folder_recursive,
            "<Control-Shift-o>": self.controller.open_folder_recursive,
        }
        
        self.FREE_SHORTCUTS = {
            "<Key-h>": self.controller.toggle_solution,
            "<Key-H>": self.controller.toggle_solution,
            "<Left>": self.controller.go_prev_file,
            "<Right>": self.controller.go_next_file,
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


class Menubar(tk.Menu):
    """GUI class for the menubar at the top of the main window.
    """
    def __init__(self, parent, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(parent, *args, **kwargs)
        
        # Set cascades
        menu_file = tk.Menu(self)
        self.add_cascade(menu=menu_file, label="File")
        menu_solving = tk.Menu(self)
        self.add_cascade(menu=menu_solving, label="Solving")
        menu_settings = tk.Menu(self)
        self.add_cascade(menu=menu_settings, label="Settings")
        
        # File
        menu_file.add_command(
            label="Open folder...",
            command=self.controller.open_folder,
            accelerator="Ctrl+O",
            underline=0,
        )
        menu_file.add_command(
            label="Open all subfolders...",
            command=self.controller.open_folder_recursive,
            accelerator="Ctrl+Shift+O",
        )
        menu_file.add_separator()
        menu_file.add_command(
            label="Copy SFEN of current position",
            command=self.controller.copy_sfen_to_clipboard,
        )
        # Solving
        menu_solving.add_command(
            label="Get statistics",
            command=self.controller.generate_statistics,
        )
        menu_solving.add_command(
            label="Export results as CSV...",
            command=self.controller.export_prob_list_csv,
        )
        menu_solving.add_separator()
        menu_solving.add_command(
            label="Clear solving statuses",
            command=self.controller.clear_statuses,
        )
        menu_solving.add_command(
            label="Clear solving times",
            command=self.controller.clear_times,
        )
        menu_solving.add_command(
            label="Clear results",
            command=self.controller.clear_results,
        )
        # Settings
        menu_settings.add_command(
            label="Settings...",
            command=lambda: SettingsWindow(controller=self.controller),
        )
        menu_settings.add_command(
            label="About tsumemi",
            command=functools.partial(
                messagebox.showinfo,
                title="About tsumemi",
                message="Written in Python 3 by Marken Foo. For the shogi community. KIF files sold separately."
            )
        )
        # Bind to main window
        parent["menu"] = self
        return


class StatisticsDialog(tk.Toplevel):
    def __init__(self, stats: plistcon.ProblemListStats,
            *args, **kwargs
        ) -> None:
        """Dialog box generating and displaying solving statistics.
        """
        super().__init__(*args, **kwargs)
        num_folder = stats.get_num_total()
        num_correct = stats.get_num_correct()
        num_wrong = stats.get_num_wrong()
        num_skip = stats.get_num_skip()
        num_seen = num_correct + num_wrong + num_skip
        total_time = stats.get_total_time()
        avg_time = (timer.Time(total_time.seconds / num_seen)
            if num_seen != 0 else timer.Time(0)
        )
        date_time_now = datetime.datetime.now()
        message_strings = [
            f"Folder name: {stats.directory}",
            f"Report generated: {date_time_now.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Total time: {total_time.to_hms_str(places=1)}",
            f"Problems in folder: {num_folder}",
            f"Problems seen: {num_seen}",
            f"Problems correct: {num_correct}",
            f"Problems wrong: {num_wrong}",
            f"Problems skipped: {num_skip}",
            f"Average time per problem: {avg_time.to_hms_str(places=1)}",
        ]
        slowest_prob = stats.get_slowest_problem()
        if slowest_prob is not None:
            _slowest_filename = os.path.basename(slowest_prob.filepath)
            _slowest_time = slowest_prob.time
            assert _slowest_time is not None
            message_strings.append(
                f"Longest time taken: {_slowest_time.to_hms_str(places=1)} ({_slowest_filename})"
            )
        fastest_prob = stats.get_fastest_problem()
        if fastest_prob is not None:
            _fastest_filename = os.path.basename(fastest_prob.filepath)
            _fastest_time = fastest_prob.time
            assert _fastest_time is not None
            message_strings.append(
                f"Shortest time taken: {_fastest_time.to_hms_str(places=1)} ({_fastest_filename})"
            )
        report_text = "\n".join(message_strings)
        
        self.title("Solving statistics")
        lbl_report = ttk.Label(self, text=report_text)
        lbl_message = ttk.Label(self, text="Copy your results from below:")
        txt_report = tk.Text(self, width=30, height=3, wrap="none")
        txt_report.insert(tk.INSERT, report_text)
        txt_report.config(state="disabled")
        vsc_txt_report = ttk.Scrollbar(self, orient="vertical", command=txt_report.yview)
        txt_report["yscrollcommand"] = vsc_txt_report.set
        hsc_txt_report = ttk.Scrollbar(self, orient="horizontal", command=txt_report.xview)
        txt_report["xscrollcommand"] = hsc_txt_report.set
        btn_ok = ttk.Button(self, text="OK", command=self.destroy)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)
        lbl_report.grid(column=0, row=0, columnspan=2)
        lbl_message.grid(column=0, row=1, columnspan=2)
        txt_report.grid(column=0, row=2, sticky="NSEW")
        vsc_txt_report.grid(column=1, row=2, sticky="NS")
        hsc_txt_report.grid(column=0, row=3, sticky="EW")
        btn_ok.grid(column=0, row=4)
        return


def run():
    logging.basicConfig(filename="tsumemilog.log", level=logging.WARNING)
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