from __future__ import annotations

import logging
import threading

# import functools
from typing import Any
from xml.dom import NotFoundErr

from pynoticenter.options import PyNotiOptions
from pynoticenter.task import PyNotiTask
from pynoticenter.task_queue import PyNotiTaskQueue


class PyNotiObserverCollection:
    __lock: threading.RLock = None
    __name: str = ""
    __fn_list: list[callable] = NotFoundErr
    __receiver_observers_dict: dict[Any, list[callable]] = None

    def __init__(self, name: str):
        self.__lock = threading.RLock()
        self.__name = name
        self.__fn_list = list[callable]()
        self.__receiver_observers_dict = dict[Any, list[callable]]()

    def add_observer(self, fn: callable, receiver: Any | None = None, *, options: PyNotiOptions | None = None):
        if fn is None:
            return

        with self.__lock:
            if receiver is None:
                self.__fn_list.append(fn)
                return

            if receiver in self.__receiver_observers_dict:
                self.__receiver_observers_dict[receiver].append(fn)
            else:
                self.__receiver_observers_dict[receiver] = list([fn])

    def remove_observer(self, fn: callable, receiver: Any | None = None):
        def remove_fn(item) -> bool:
            return item == fn

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
        fn_list = list()
        with self.__lock:
            fn_list.extend(self.__fn_list)
            for _, v in self.__receiver_observers_dict.items():
                fn_list.extend(v)
        for fn in fn_list:
            fn(*args, **kwargs)


class PyNotiCenter:
    global __default_global_instance
    __default_global_instance = None
    global __default_global_lock
    __default_global_lock = threading.RLock()

    __lock: threading.RLock = None
    __default_queue: PyNotiTaskQueue = None
    __task_queue_dict: dict[str, PyNotiTaskQueue] = None
    __unnamed_task_queue: list[PyNotiTaskQueue] = None
    __notifications_dict: dict[str, PyNotiObserverCollection] = None

    __is_shutdown: bool = False

    def __init__(self):
        self.__lock = threading.RLock()
        self.__default_queue = PyNotiTaskQueue(None)
        self.__task_queue_dict = dict[str, PyNotiTaskQueue]()
        self.__unnamed_task_queue = list[PyNotiTaskQueue]()
        self.__notifications_dict = dict[str, PyNotiObserverCollection]()

    @staticmethod
    def default() -> PyNotiCenter:
        global __default_global_lock
        global __default_global_instance
        with __default_global_lock:
            if __default_global_instance is None:
                __default_global_instance = PyNotiCenter()
        return __default_global_instance

    def post_task(self, fn: callable, *args: Any, **kwargs: Any) -> str:
        """Post task to default task queue."""
        return self.post_task_with_delay(0, fn, *args, **kwargs)

    def post_task_with_delay(self, delay: int, fn: callable, *args: Any, **kwargs: Any) -> str:
        """Post task with delay to default task queue."""
        with self.__lock:
            return self.__default_queue.schedule_task_with_delay(delay, fn, *args, **kwargs)

    def post_task_to_task_queue(self, queue_name: str, fn: callable, *args: Any, **kwargs: Any) -> str:
        with self.__lock:
            q = self.get_task_queue(queue_name)
            if q is None:
                q = self.create_task_queue(queue_name)
            return q.schedule_task(fn, *args, **kwargs)

    def cancel_task(self, task_id):
        with self.__lock:
            self.__default_queue.cancel_task(task_id)

    def cancel_task_with_queue_name(self, queue_name: str, task_id: str):
        queue = self.get_task_queue(queue_name)
        if queue is not None:
            queue.cancel_task(task_id)

    def shutdown(self, wait: bool):
        """Shutdown all tasks, include the unnamed task queue.

        Args:
            wait (bool): wait until all task done.
        """
        task_queues = list[PyNotiTaskQueue]()
        with self.__lock:
            # mark shutdown
            self.__is_shutdown = True
            for q in self.__unnamed_task_queue:
                task_queues.append(q)
            self.__unnamed_task_queue.clear()
            for _, q in self.__task_queue_dict.items():
                task_queues.append(q)
            self.__task_queue_dict.clear()
        # terminate other task queue
        for q in task_queues:
            q.terminate(wait)
        # terminate default task queue
        self.__default_queue.terminate(wait)

    def release_task_queue(self, queue_name: str, wait: bool):
        """release task queue resource.

        Args:
            queue_name (str): queue name
            wait (bool): wait until task done
        """
        if queue_name is None:
            return
        with self.__lock:
            if queue_name in self.__task_queue_dict:
                queue = self.__task_queue_dict.pop(queue_name)
                queue.terminate(wait)

    def create_task_queue(self, queue_name: str) -> PyNotiTaskQueue:
        """Create task queue by name.

        If name always exist, it will return the existen queue.
        If name is None, it will create unnamed task queue.

        Args:
            queue_name (str): queue name

        Returns:
            PyNotiTaskQueue: task queue
        """
        if queue_name is None:
            queue = PyNotiTaskQueue(queue_name)
            with self.__lock:
                self.__unnamed_task_queue.add(queue)
                self.__unnamed_task_queue = [queue for queue in self.__unnamed_task_queue if not queue.is_terminated]
            return queue

        with self.__lock:
            if queue_name in self.__task_queue_dict:
                return self.__task_queue_dict[queue_name]

        queue = PyNotiTaskQueue(queue_name)
        with self.__lock:
            self.__task_queue_dict[queue_name] = queue
        return queue

    def get_default_task_queue(self) -> PyNotiTaskQueue:
        with self.__lock:
            return self.__default_queue

    def get_task_queue(self, queue_name: str) -> PyNotiTaskQueue:
        """Get task queue from notification center.

        If name is None, return default task queue.

        Args:
            queue_name (str): queue name

        Returns:
            PyNotiTaskQueue: return task queue
        """

        if queue_name is None:
            return self.__default_queue

        with self.__lock:
            if queue_name in self.__task_queue_dict:
                return self.__task_queue_dict[queue_name]

    def add_observer(
        self, name: str, fn: callable, receiver: Any | None = None, *, options: PyNotiOptions | None = None
    ):
        """add notification observer"""
        with self.__lock:
            observer_collection: PyNotiObserverCollection = None
            if name in self.__notifications_dict:
                observer_collection = self.__notifications_dict[name]

            if observer_collection is None:
                observer_collection = PyNotiObserverCollection(name)

            observer_collection.add_observer(fn, receiver, options=options)
            self.__notifications_dict[name] = observer_collection

    def remove_observer(self, name: str, fn: callable, receiver: Any | None = None):
        observer_collection = self.__get_notification_observer_collection__(name)
        if observer_collection is not None:
            observer_collection.remove_observer(fn, receiver)

    def remove_observers(self, receiver: Any):
        with self.__lock:
            for _, observer_collection in self.__notifications_dict.items():
                observer_collection.remove_observers(receiver)

    def remove_all_observers(self):
        with self.__lock:
            for _, observer_collection in self.__notifications_dict.items():
                observer_collection.remove_all_observers()
            self.__notifications_dict.clear()

    def notify_observers(self, name: str, *args: Any, **kwargs: Any):
        """post notification"""
        self.__default_queue.post_task(self.__notify_observers__, name, *args, **kwargs)

    def __get_notification_observer_collection__(self, name: str) -> PyNotiObserverCollection:
        observer_collection: PyNotiObserverCollection = None
        with self.__lock:
            if name in self.__notifications_dict:
                observer_collection = self.__notifications_dict[name]
        return observer_collection

    def __notify_observers__(self, name: str, *args: Any, **kwargs: Any):
        observer_collection = self.__get_notification_observer_collection__(name)
        if observer_collection is not None:
            observer_collection.notify_observers(*args, **kwargs)
