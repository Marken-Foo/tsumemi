from __future__ import annotations

import datetime
import logging.config
import os
import tkinter as tk

from tkinter import filedialog, ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.game.game_controller as gamecon
import tsumemi.src.tsumemi.notation_writer as nwriter
import tsumemi.src.tsumemi.problem_list.problem_list_model as plist
import tsumemi.src.tsumemi.problem_list.problem_list_controller as plistcon
import tsumemi.src.tsumemi.settings.settings_controller as setcon
import tsumemi.src.tsumemi.speedrun_controller as speedcon
import tsumemi.src.tsumemi.timer_controller as timecon

from tsumemi.src.shogi.parsing import kif
from tsumemi.src.tsumemi import files, timer
from tsumemi.src.tsumemi.main_window_view import MainWindowView
from tsumemi.src.tsumemi.menubar import Menubar
from tsumemi.src.tsumemi.statistics_window import StatisticsDialog

if TYPE_CHECKING:
    from typing import Callable, Optional
    import tsumemi.src.tsumemi.img_handlers as imghand
    from tsumemi.src.shogi import notation
    from tsumemi.src.shogi.game import Game


class RootController(evt.IObserver):
    """Root controller for the application. Manages top-level logic
    and GUI elements.
    """
    # eventually, refactor menu labels and dialog out into a constant namespace
    def __init__(self, root: tk.Tk) -> None:
        evt.IObserver.__init__(self)
        # Program data
        self.settings = setcon.Settings(self)
        self.skin_settings = self.settings.get_skin_settings()
        self.notation_writer = nwriter.NotationWriter(
            self.settings.notation_controller.get_move_writer()
        )
        self.main_game = gamecon.GameController(self.notation_writer)
        self.main_timer = timecon.TimerController()
        self.main_problem_list = plistcon.ProblemListController()

        self.speedrun_controller = speedcon.SpeedrunController(self)

        self.main_game.add_observer(
            self.speedrun_controller._speedrun_states["question"]
        )
        self.main_timer.clock.add_observer(self)
        self.main_problem_list.problem_list.add_observer(self)
        self.set_callbacks({
            timer.TimerSplitEvent: self._on_split,
            plist.ProbSelectedEvent: self._on_prob_selected,
        })

        # GUI
        self.root: tk.Tk = root
        root.option_add("*tearOff", False)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        root.title("tsumemi")

        self.menubar: Menubar = Menubar(parent=self.root, controller=self)

        self.mainframe: MainWindowView = MainWindowView(root, self)
        self.mainframe.grid_items_normal()

        # Keyboard shortcuts
        self.bindings = Bindings(self)
        self.bindings.bind_shortcuts(self.root, self.bindings.MASTER_SHORTCUTS)
        self.bindings.bind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return

    def open_settings_window(self) -> None:
        self.settings.open_settings_window()
        return

    def open_folder(self,
            _event: Optional[tk.Event] = None, recursive: bool = False
        ) -> None:
        """Prompt user for a folder, open into main_problem_list.
        """
        directory = filedialog.askdirectory()
        if not directory:
            return
        directory = os.path.normpath(directory)
        kif_files = files.get_kif_files(directory, recursive)
        self.main_problem_list.set_directory(
            directory, kif_files
        )
        return

    def open_folder_recursive(self, _event: Optional[tk.Event] = None) -> None:
        return self.open_folder(recursive=True)

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
        self.mainframe.refresh_main_board()
        self.mainframe.refresh_move_list()
        self.mainframe.enable_move_input()
        self.mainframe.hide_solution()
        self.root.title("tsumemi - " + str(prob.filepath))
        return

    def _read_problem(self, prob: plist.Problem) -> None:
        """Read the problem data from file into the program.
        """
        game = self.game_from_problem(prob)
        if game is None:
            return
        self.mainframe.set_solution(self.solution_str_from_game(game))
        self.main_game.set_game(game)
        return

    def game_from_problem(self, prob: plist.Problem) -> Optional[Game]:
        filepath = prob.filepath
        if filepath is None:
            return None
        return kif.read_kif(filepath)

    def solution_str_from_game(self, game: Game) -> str:
        return "　".join(self.notation_writer.write_mainline(game))

    def refresh_solution_text(self) -> None:
        game = self.main_game.game.game
        self.mainframe.set_solution(self.solution_str_from_game(game))
        # force view to update
        self.mainframe.toggle_solution()
        self.mainframe.toggle_solution()
        return

    def go_next_file(self, _event: Optional[tk.Event] = None) -> bool:
        prob = self.main_problem_list.go_next_problem()
        return prob is not None

    def go_prev_file(self, _event: Optional[tk.Event] = None) -> bool:
        prob = self.main_problem_list.go_prev_problem()
        return prob is not None

    def go_to_file(self, _event: Optional[tk.Event] = None, idx: int = 0
        ) -> bool:
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
        if not directory:
            return
        self.main_problem_list.export_as_csv(directory)
        return

    #=== Speedrun controller commands
    def start_speedrun(self) -> None:
        self.speedrun_controller.start_speedrun()
        self.mainframe.btn_speedrun.config(state="disabled")
        self.mainframe.btn_abort_speedrun.config(state="normal")
        self.bindings.unbind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return

    def abort_speedrun(self) -> None:
        self.speedrun_controller.abort_speedrun()
        self.update_nav_control_pane(self.mainframe.make_nav_pane_normal)
        self.mainframe.btn_speedrun.config(state="normal")
        self.mainframe.btn_abort_speedrun.config(state="disabled")
        self.bindings.bind_shortcuts(self.root, self.bindings.FREE_SHORTCUTS)
        return

    def update_nav_control_pane(self,
            nav_pane_constructor: Callable[[tk.Widget], ttk.Frame]
        ) -> None:
        self.mainframe.update_nav_control_pane(nav_pane_constructor)
        return

    #=== GUI display methods
    def apply_skin_settings(self, settings: imghand.SkinSettings) -> None:
        self.skin_settings = settings
        self.mainframe.apply_skins(settings)
        return

    def apply_notation_settings(self, move_writer: notation.AbstractMoveWriter
        ) -> None:
        self.notation_writer.change_move_writer(move_writer)
        self.refresh_solution_text()
        self.mainframe.movelist_frame.refresh_content()
        return

    #=== Observer callbacks
    def _on_split(self, event: timer.TimerSplitEvent) -> None:
        if self.main_timer.clock is event.clock:
            self.main_problem_list.set_time(event.time)
        return

    def _on_prob_selected(self, event: plist.ProbSelectedEvent) -> None:
        if event.sender is self.main_problem_list.problem_list:
            self.show_problem(event.problem)
        return


class Bindings:
    # Just to group all shortcut bindings together for convenience.
    def __init__(self, controller: RootController):
        self.controller: RootController = controller

        self.MASTER_SHORTCUTS = {
            "<Control-o>": self.controller.open_folder,
            "<Control-O>": self.controller.open_folder,
            "<Control-Shift-O>": self.controller.open_folder_recursive,
            "<Control-Shift-o>": self.controller.open_folder_recursive,
        }

        self.FREE_SHORTCUTS = {
            "<Key-h>": self.controller.mainframe.toggle_solution,
            "<Key-H>": self.controller.mainframe.toggle_solution,
            "<Key-Left>": self.controller.go_prev_file,
            "<Key-Right>": self.controller.go_next_file,
        }

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


def run() -> None:
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
    RootController(root)
    apply_theme_fix()
    root.minsize(width=400, height=200) # stopgap vs canvas overshrinking bug
    root.mainloop()
