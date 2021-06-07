from __future__ import annotations

import tkinter as tk

from tkinter import ttk
from typing import TYPE_CHECKING

import tsumemi.src.tsumemi.event as evt
import tsumemi.src.tsumemi.timer as timer

if TYPE_CHECKING:
    from typing import Optional


class TimerController:
    """Controller object for a stopwatch timer. Handles access to its
    timer (model).
    """
    def __init__(self) -> None:
        self.clock: timer.Timer = timer.Timer()
        return
    
    def make_timer_pane(self, parent: tk.Widget, *args, **kwargs) -> TimerPane:
        return TimerPane(parent, self.clock, *args, **kwargs)
    
    def start(self) -> None:
        return self.clock.start()
    
    def stop(self) -> None:
        return self.clock.stop()
    
    def reset(self) -> None:
        return self.clock.reset()
    
    def split(self) -> Optional[float]:
        return self.clock.split()


class TimerDisplay(ttk.Label, evt.IObserver):
    """GUI class to display a stopwatch/timer.
    """
    def __init__(self, parent: tk.Widget, clock: timer.Timer, *args, **kwargs
        ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.clock: timer.Timer = clock
        self.clock.add_observer(self)
        self.NOTIFY_ACTIONS = {
            timer.TimerStartEvent: self._on_start,
            timer.TimerStopEvent: self._on_stop
        }
        # Assume timer is in reset state, initialise to match
        self.is_running: bool = False
        self.time_str: tk.StringVar = tk.StringVar(value=timer.sec_to_str(0.0))
        
        self["textvariable"] = self.time_str
        self.configure(
            background="black",
            foreground="light sky blue",
            font=("TkDefaultFont", 48)
        )
    
    def _on_start(self, event: evt.Event) -> None:
        self.is_running = True
        self.refresh()
        return
        
    def _on_stop(self, event: evt.Event) -> None:
        self.is_running = False
        self.refresh()
        return
    
    def refresh(self) -> None:
        self.time_str.set(
            timer.sec_to_str(
                self.clock.read()
            )
        )
        if self.is_running:
            self.after(40, self.refresh)
        return


class TimerPane(ttk.Frame):
    """GUI frame containing a timer display and associated controls.
    """
    def __init__(self, parent: tk.Widget, clock: timer.Timer, *args, **kwargs
        ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.timer_display: TimerDisplay = TimerDisplay(
            parent=self,
            clock=clock
        )
        
        self.timer_display.grid(
            column=0, row=0, columnspan=3
        )
        ttk.Button(
            self, text="Start/stop timer",
            command=clock.toggle
        ).grid(
            column=0, row=1
        )
        ttk.Button(
            self, text="Reset timer",
            command=clock.reset
        ).grid(
            column=1, row=1
        )
        ttk.Button(
            self, text="Split",
            command=clock.split
        ).grid(
            column=2, row=1
        )
        return
