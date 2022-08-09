from __future__ import annotations

import datetime
import os
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.timer as timer

if TYPE_CHECKING:
    import tsumemi.src.tsumemi.problem_list_controller as plistcon


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
        lbl_report.grid(row=0, column=0, columnspan=2)
        lbl_message.grid(row=1, column=0, columnspan=2)
        txt_report.grid(row=2, column=0, sticky="NSEW")
        vsc_txt_report.grid(row=2, column=1, sticky="NS")
        hsc_txt_report.grid(row=3, column=0, sticky="EW")
        btn_ok.grid(row=4, column=0)
        return
