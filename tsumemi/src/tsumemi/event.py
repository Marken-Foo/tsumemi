from __future__ import annotations

import weakref

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Type
    from weakref import ReferenceType


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
        return

    def on_notify(self, event: Event) -> None:
        event_type = type(event)
        if event_type in self.NOTIFY_ACTIONS:
            self.NOTIFY_ACTIONS[event_type](event)
        return

    def add_notification(self, event: Type[Event], func: Callable[..., Any]
        ) -> None:
        self.NOTIFY_ACTIONS[event] = func
        return


class Emitter():
    """Base class for any class that needs to emit events.
    """
    def __init__(self) -> None:
        self.observer_refs: List[ReferenceType[IObserver]] = []
        return

    def add_observer(self, observer: IObserver) -> None:
        self.observer_refs.append(weakref.ref(observer))
        return

    def remove_observer(self, observer: IObserver) -> None:
        self.observer_refs = [
            ref for ref in self.observer_refs
            if ref() is not None and ref() is not observer
        ]
        return

    def _notify_observers(self, event: Event) -> None:
        self.observer_refs = [
            ref for ref in self.observer_refs if ref() is not None
        ]
        for ref in self.observer_refs:
            observer = ref()
            # Still check, just in case the gc collected something
            if observer is not None:
                observer.on_notify(event)
        return
