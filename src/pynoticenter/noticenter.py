from __future__ import annotations

import asyncio
import queue
import threading

# import functools
from typing import Any

from pynoticenter.task import PyNotiTask
from pynoticenter.task_queue import PyNotiTaskQueue


class PyNotiCenter:
    global __default_global_instance
    __default_global_instance = None
    global __default_global_lock
    __default_global_lock = threading.RLock()

    __task_queue: PyNotiTaskQueue = None
    __task_queue_dict: dict[str, PyNotiTaskQueue] = None
    __unnamed_task_queue: list[PyNotiTaskQueue] = None
    __lock: threading.RLock = None
    __is_shutdown: bool = False

    def __init__(self):
        self.__lock = threading.RLock()
        self.__task_queue = PyNotiTaskQueue(None)
        self.__task_queue_dict = dict[str, PyNotiTaskQueue]()
        self.__unnamed_task_queue = list[PyNotiTaskQueue]()

    @staticmethod
    def default_center() -> PyNotiCenter:
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
            return self.__task_queue.schedule_task_with_delay(delay, fn, *args, **kwargs)

    def post_task_to_task_queue(self, queue_name: str, fn: callable, *args: Any, **kwargs: Any) -> str:
        with self.__lock:
            q = self.get_task_queue(queue_name)
            if q is None:
                q = self.create_task_queue(queue_name)
            return q.schedule_task(fn, *args, **kwargs)

    def cancel_task(self, task_id):
        with self.__lock:
            self.__task_queue.cancel_task(task_id)

    def cancel_task_with_queue_name(self, queue_name: str, task_id: str):
        queue = self.get_task_queue(queue_name)
        if queue is not None:
            queue.cancel_task(task_id)

    def shutdown(self, wait: bool):
        """Shutdown all tasks, include the unnamed task queue.

        Args:
            wait (bool): wait until all task done.
        """
        task_queue = list[PyNotiTaskQueue]()
        with self.__lock:
            # mark shutdown
            self.__is_shutdown = True
            for q in self.__unnamed_task_queue:
                task_queue.append(q)
            self.__unnamed_task_queue.clear()
            for _, q in self.__task_queue_dict.items():
                task_queue.append(q)
            self.__task_queue_dict.clear()
        # terminate other task queue
        for q in task_queue:
            q.terminate(wait)
        # terminate default task queue
        with self.__lock:
            self.__task_queue.terminate(wait)

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
            return self.__task_queue

    def get_task_queue(self, queue_name: str) -> PyNotiTaskQueue:
        """Get task queue from notification center.

        If name not exist, return None.

        Args:
            queue_name (str): queue name

        Returns:
            PyNotiTaskQueue: return task queue
        """

        if queue_name is None:
            return None

        with self.__lock:
            if queue_name in self.__task_queue_dict:
                return self.__task_queue_dict[queue_name]

    def register_notification(self, name: str, fn: callable):
        """register notification"""
        pass

    def notify(self, name: str, *args: Any, **kwargs: Any):
        """post notification"""
        pass
