from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Type


class Event:
    """Base class for Events of all kinds.
    """
    def __init__(self) -> None:
        return


class IObserver(ABC):
    """Base class for any class that needs to observe events.
    """
    def __init__(self) -> None:
        self.NOTIFY_ACTIONS: Dict[Type[Event], Callable[..., Any]] = {}
    
    @abstractmethod
    def on_notify(self, event: Event) -> None:
        event_type = type(event)
        if event_type in self.NOTIFY_ACTIONS:
            self.NOTIFY_ACTIONS[event_type](event)
        return


class Emitter():
    """Base class for any class that needs to emit events.
    """
    def __init__(self) -> None:
        self.observers: List[IObserver] = []
        return
    
    def add_observer(self, observer: IObserver) -> None:
        self.observers.append(observer)
        return
    
    def remove_observer(self, observer: IObserver) -> None:
        try:
            self.observers.remove(observer)
        except ValueError:
            # observer does not exist in list; log
            pass
        return
    
    def _notify_observers(self, event: Event) -> None:
        for observer in self.observers:
            observer.on_notify(event)
        return