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
        self.__task_queue_dict = dict()
        self.__unnamed_task_queue = list()

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

    def post_task_to_task_queue(self, queue_name: str, task: callback, **kwargs: Any) -> str:
        with self.__lock:
            queue = self.get_task_queue(queue_name)
            return queue.schedule_task(task, **kwargs)

    def cancel_task(self, task_id):
        with self.__lock:
            self.__task_queue.cancel_task(task_id)

    def cancel_task_with_queue_name(self, queue_name: str, task_id: str):
        queue = self.get_task_queue(queue_name)
        queue.cancel_task(task_id)

    def shutdown(self, wait: bool):
        """Shutdown all tasks, include the unnamed task queue."""
        task_queue = list[PyNotiTaskQueue]()
        with self.__lock:
            # mark shutdown
            self.__is_shutdown = True
            for _, q in self.__task_queue_dict.items():
                task_queue.append(q)
            self.__task_queue_dict.clear()
        # terminate other task queue
        for q in task_queue:
            q.terminate(wait)
        # terminate default task queue
        with self.__lock:
            self.__task_queue.terminate(wait)

    def get_task_queue(self, queue_name: str) -> PyNotiTaskQueue:
        """Get task queue from notification center.

        All task queue will manage by notification center. If the queue name doesn't exist, it will create one and return.
        If you pass an None value for queue_name, it means it will retuan an unnamed task queue.

        Args:
            queue_name (str): queue name

        Returns:
            PyNotiTaskQueue: return task queue
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
