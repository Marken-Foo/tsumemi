from __future__ import annotations

import datetime
import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

from tsumemi.src.tsumemi.run_statistics import RunStatistics

if TYPE_CHECKING:
    from typing import Any


class StatisticsDialog(tk.Toplevel):
    def __init__(self, stats: RunStatistics, *args: Any, **kwargs: Any) -> None:
        """Dialog box generating and displaying solving statistics."""
        super().__init__(*args, **kwargs)

        date_time_now = datetime.datetime.now()
        message_strings = [
            f"Folder name: {stats.directory_name}",
            f"Report generated: {date_time_now.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Total time: {stats.total_time.to_hms_str(places=1)}",
            f"Problems in folder: {stats.total_problems}",
            f"Problems seen: {stats.total_seen}",
            f"Problems correct: {stats.total_correct}",
            f"Problems wrong: {stats.total_wrong}",
            f"Problems skipped: {stats.total_skipped}",
            f"Average time per problem: {stats.average_time_per_problem.to_hms_str(places=1)}",
        ]
        slowest_problem = stats.slowest_problem
        if slowest_problem is not None and slowest_problem.time is not None:
            message_strings.append(
                f"Longest time taken: {slowest_problem.time.to_hms_str(places=1)} ({slowest_problem.name})"
            )
        fastest_problem = stats.fastest_problem
        if fastest_problem is not None and fastest_problem.time is not None:
            message_strings.append(
                f"Shortest time taken: {fastest_problem.time.to_hms_str(places=1)} ({fastest_problem.name})"
            )
        report_text = "\n".join(message_strings)

        self.title("Solving statistics")
        lbl_report = ttk.Label(self, text=report_text)
        lbl_message = ttk.Label(self, text="Copy your results from below:")
        txt_report = tk.Text(self, width=30, height=3, wrap="none")
        txt_report.insert(tk.INSERT, report_text)
        txt_report.config(state="disabled")
        vsc_txt_report = ttk.Scrollbar(
            self, orient="vertical", command=txt_report.yview
        )
        txt_report["yscrollcommand"] = vsc_txt_report.set
        hsc_txt_report = ttk.Scrollbar(
            self, orient="horizontal", command=txt_report.xview
        )
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
