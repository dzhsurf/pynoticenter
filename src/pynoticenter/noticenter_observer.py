"""PyNotiObserver"""
import threading
from typing import Any, Callable, Dict, List, Optional

from pynoticenter.options import PyNotiOptions


class PyNotiObserver(object):
    def __init__(self, fn: Callable[..., Any], options: Optional[PyNotiOptions]):
        self.__fn: Callable[..., Any] = fn
        self.__options: Optional[PyNotiOptions] = options

    @property
    def fn(self) -> Callable[..., Any]:
        return self.__fn

    @property
    def options(self) -> PyNotiOptions:
        if self.__options is None:
            self.__options = PyNotiOptions(queue=f"{id(self)}")
        return self.__options


class PyNotiObserverCollection:
    def __init__(self, name: str, scheduler: Callable[..., Any]):
        self.__name: str = name
        self.__scheduler = scheduler
        self.__lock: threading.RLock = threading.RLock()
        self.__fn_list: List[PyNotiObserver] = []
        self.__receiver_observers_dict: Dict[Any, List[PyNotiObserver]] = {}

    def add_observer(self, fn: Callable[..., Any], receiver: Any = None, *, options: Optional[PyNotiOptions] = None):
        if fn is None:
            return

        with self.__lock:
            if receiver is None:
                self.__fn_list.append(PyNotiObserver(fn, options))
                return

            if receiver in self.__receiver_observers_dict:
                self.__receiver_observers_dict[receiver].append(PyNotiObserver(fn, options))
            else:
                self.__receiver_observers_dict[receiver] = list([PyNotiObserver(fn, options)])

    def remove_observer(self, fn: Callable[..., Any], receiver: Any = None):
        def remove_fn(item: PyNotiObserver) -> bool:
            return item.fn == fn

        with self.__lock:
            if receiver is None:
                self.__fn_list = list(filter(remove_fn, self.__fn_list))
                return

            if receiver not in self.__receiver_observers_dict:
                return

            observers = self.__receiver_observers_dict.pop(receiver)
            observers = list(filter(remove_fn, observers))
            if len(observers) > 0:
                self.__receiver_observers_dict[receiver] = observers

    def remove_observers(self, receiver: Any):
        if receiver is None:
            return
        with self.__lock:
            if receiver in self.__receiver_observers_dict:
                self.__receiver_observers_dict.pop(receiver)

    def remove_all_observers(self):
        with self.__lock:
            self.__fn_list.clear()
            self.__receiver_observers_dict.clear()

    def notify_observers(self, *args: Any, **kwargs: Any):
        observers = list[PyNotiObserver]()
        with self.__lock:
            observers.extend(self.__fn_list)
            for _, v in self.__receiver_observers_dict.items():
                observers.extend(v)
        for observer in observers:
            self.__scheduler(observer, *args, **kwargs)
