from __future__ import annotations

import weakref

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any
    from weakref import ReferenceType


class Event:
    """Base class for Events of all kinds."""

    def __init__(self) -> None:
        return


class IObserver(ABC):
    """Base class for any class that needs to observe events."""

    def __init__(self) -> None:
        self._notify_actions: dict[type[Event], Callable[..., Any]] = {}

    def on_notify(self, event: Event) -> None:
        event_type = type(event)
        if event_type in self._notify_actions:
            self._notify_actions[event_type](event)

    def set_callbacks(
        self, notification_dict: dict[type[Event], Callable[..., Any]]
    ) -> None:
        self._notify_actions = notification_dict

    def add_callback(self, event: type[Event], func: Callable[..., Any]) -> None:
        self._notify_actions[event] = func


class Emitter:
    """Base class for any class that needs to emit events."""

    def __init__(self) -> None:
        self.observer_refs: list[ReferenceType[IObserver]] = []

    def add_observer(self, observer: IObserver) -> None:
        self.observer_refs.append(weakref.ref(observer))

    def remove_observer(self, observer: IObserver) -> None:
        self.observer_refs = [
            ref
            for ref in self.observer_refs
            if ref() is not None and ref() is not observer
        ]

    def _notify_observers(self, event: Event) -> None:
        self.observer_refs = [ref for ref in self.observer_refs if ref() is not None]
        for ref in self.observer_refs:
            observer = ref()
            # Still check, just in case the gc collected something
            if observer is not None:
                observer.on_notify(event)
