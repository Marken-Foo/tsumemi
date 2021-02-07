from abc import ABC, abstractmethod


class Event:
    """Base class for Events of all kinds.
    """
    def __init__(self):
        pass


class IObserver(ABC):
    """Base class for any class that needs to observe events.
    """
    @abstractmethod
    def on_notify(event):
        event_type = type(event)
        if event_type in self.NOTIFY_ACTIONS:
            self.NOTIFY_ACTIONS[event_type](event)
        return


class Emitter():
    """Base class for any class that needs to emit events.
    """
    def add_observer(self, observer):
        self.observers.append(observer)
        return
    
    def remove_observer(self, observer):
        try:
            self.observers.remove(observer)
        except ValueError:
            # observer does not exist in list; log
            pass
        return
    
    def _notify_observers(self, event):
        for observer in self.observers:
            observer.on_notify(event)
        return