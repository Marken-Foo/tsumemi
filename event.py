from abc import ABC, abstractmethod


class Event:
    def __init__(self):
        pass

class ProbDirEvent(Event):
    def __init__(self, prob_list):
        self.prob_list = prob_list

class ProbStatusEvent(Event):
    def __init__(self, prob_idx, status):
        self.idx = prob_idx
        self.status = status

class ProbTimeEvent(Event):
    def __init__(self, prob_idx, time):
        self.idx = prob_idx
        self.time = time

class TimerStartEvent(Event):
    pass

class TimerStopEvent(Event):
    pass

class TimerSplitEvent(Event):
    def __init__(self, lap_time):
        self.time = lap_time


class IObserver(ABC):
    @abstractmethod
    def on_notify(event):
        pass

class Emitter():
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