import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional

from pynoticenter.noticenter_observer import PyNotiObserver, PyNotiObserverCollection
from pynoticenter.options import PyNotiOptions
from pynoticenter.task_queue import PyNotiTaskQueue


class PyNotiCenterInterface(ABC):
    """PyNotiCenter Interface"""

    @abstractmethod
    def post_task(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """post task to default task queue.

        Args:
            fn (Callable[..., None]): callback function
            *args (Any): args
            **kwargs (Any): kwargs

        Returns:
            str: return task id
        """
        pass

    @abstractmethod
    def post_task_with_delay(self, delay: float, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """post task to default task queue with delay.

        Args:
            fn (Callable[..., None]): callback function
            delay (float): delay time in seconds.
            *args (Any): args
            **kwargs (Any): kwargs

        Returns:
            str: return task id
        """
        pass

    @abstractmethod
    def post_task_to_task_queue(self, queue_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """post task to named task queue.

        Args:
            fn (Callable[..., None]): callback function
            queue_name (str): queue name, create from create_task_queue
            *args (Any): args
            **kwargs (Any): kwargs

        Returns:
            str: return task id
        """
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> None:
        """cancel task from default task queue with task id

        Args:
            task_id (str): task id

        """
        pass

    @abstractmethod
    def cancel_task_with_queue_name(self, queue_name: str, task_id: str):
        """cancel task from named task queue with task id

        Args:
            queue_name (str): task queue name
            task_id (str): task id

        """
        pass

    @abstractmethod
    def wait_until_task_complete(self):
        """wait until all task complete. it will block until there is no task."""
        pass

    @abstractmethod
    def shutdown(self, wait: bool):
        """shutdown PyNotiCenter. Once shutdown, you can't call it anymore.

        When shutdown is called, you can not post new task to task queue, all task queue will ignore the new task.
        When wait is setted, it will block until all task complete, if not set, all task queue will shutdown as fast as possible.

        Args:
            wait (bool): set wait for task complete or not.

        """
        pass

    @abstractmethod
    def release_task_queue(self, queue_name: str, wait: bool):
        """release task queue

        Args:
            queue_name (str): task queue name
            wait (bool): wait for wait complete.

        """
        pass

    @abstractmethod
    def create_task_queue(self, options: PyNotiOptions) -> PyNotiTaskQueue:
        """create task queue with name

        Args:
            options (PyNotiOptions): task queue options

        Returns:
            PyNotiTaskQueue: task queue

        """
        pass

    @abstractmethod
    def get_default_task_queue(self) -> PyNotiTaskQueue:
        """return default task queue

        Returns:
            PyNotiTaskQueue: default task queue
        """
        pass

    @abstractmethod
    def get_task_queue(self, queue_name: str) -> PyNotiTaskQueue:
        """return named task queue

        Args:
            queue_name (str): task queue name

        Returns:
            PyNotiTaskQueue: task queue
        """
        pass

    @abstractmethod
    def add_observer(
        self, name: str, fn: Callable[..., Any], receiver: Any = None, *, options: Optional[PyNotiOptions] = None
    ) -> None:
        """Add observer to PyNotiCenter

        Args:
            name (str): notification name
            fn (Callable[..., None]): callback function
            receiver (Any): receiver object
            options (Optional[PyNotiOptions]): options
        """
        pass

    @abstractmethod
    def remove_observer(self, name: str, fn: Callable[..., Any], receiver: Optional[Any] = None) -> None:
        """Remove observer from PyNotiCenter

        Args:
            name (str): notification name
            fn (Callable[..., None]): callback function
            receiver (Optional[Any]): receiver object
        """
        pass

    @abstractmethod
    def remove_observers(self, receiver: Any) -> None:
        """Remove observers from PyNotiCenter

        Args:
            receiver (Any): receiver object
        """
        pass

    @abstractmethod
    def remove_all_observers(self) -> None:
        """Remove all observers from PyNotiCenter"""
        pass

    @abstractmethod
    def notify_observers(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Notify observers

        Args:
            name (str): notification name
            *args (Any): args
            **kwargs (Any): kwargs
        """
        pass


class PyNotiCenter(PyNotiCenterInterface):
    """PyNotiCenter Implement

    :meta private:
    """

    global __default_global_instance
    __default_global_instance = None
    global __default_global_lock
    __default_global_lock = threading.RLock()

    def __init__(self):
        self.__lock: threading.RLock = threading.RLock()
        self.__common_thread_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)
        self.__scheduler_runloop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.__scheduler_thread: threading.Thread = threading.Thread(target=self.__scheduler_thread__)
        self.__default_queue: PyNotiTaskQueue = PyNotiTaskQueue(
            None, self.__scheduler_runloop, self.__common_thread_pool
        )
        self.__task_queue_dict: Dict[str, PyNotiTaskQueue] = {}
        self.__unnamed_task_queue: List[PyNotiTaskQueue] = []
        self.__notifications_dict: Dict[str, PyNotiObserverCollection] = {}
        self.__scheduler_thread.start()

        self.__is_shutdown: bool = False

    @staticmethod
    def default() -> PyNotiCenterInterface:
        global __default_global_lock
        global __default_global_instance
        with __default_global_lock:
            if __default_global_instance is None:
                __default_global_instance = PyNotiCenter()
        return __default_global_instance

    def post_task(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        return self.post_task_with_delay(0, fn, *args, **kwargs)

    def post_task_with_delay(self, delay: float, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        with self.__lock:
            return self.__default_queue.post_task_with_delay(delay, fn, *args, **kwargs)

    def post_task_to_task_queue(self, queue_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        with self.__lock:
            q: Optional[PyNotiTaskQueue] = None
            try:
                q = self.get_task_queue(queue_name)
            except:
                q = self.create_task_queue(PyNotiOptions(queue=queue_name))
            if q is not None:
                return q.post_task(fn, *args, **kwargs)
        return ""

    def cancel_task(self, task_id: str):
        with self.__lock:
            self.__default_queue.cancel_task(task_id)

    def cancel_task_with_queue_name(self, queue_name: str, task_id: str):
        queue = self.get_task_queue(queue_name)
        if queue is not None:
            queue.cancel_task(task_id)

    def wait_until_task_complete(self):
        event = threading.Event()
        while not event.is_set():
            wait = False
            with self.__lock:
                for q in self.__unnamed_task_queue:
                    if q.task_count > 0:
                        wait = True
                    if wait:
                        break
                for _, q in self.__task_queue_dict.items():
                    if q.task_count > 0:
                        wait = True
                    if wait:
                        break
                if self.__default_queue.task_count > 0:
                    wait = True
            if not wait:
                event.set()
            else:
                event.wait(timeout=0.5)

    def shutdown(self, wait: bool):
        logging.info(f"PyNotiCenter start shutdown, wait = {wait}")
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
        # exit scheduler thread
        def stop_scheduler_runloop():
            self.__scheduler_runloop.stop()

        self.__scheduler_runloop.call_soon_threadsafe(stop_scheduler_runloop)
        logging.info("PyNotiCenter shutdown end")

    def release_task_queue(self, queue_name: str, wait: bool):
        if queue_name is None:
            return
        with self.__lock:
            if queue_name in self.__task_queue_dict:
                queue = self.__task_queue_dict.pop(queue_name)
                queue.terminate(wait)

    def create_task_queue(self, options: PyNotiOptions) -> PyNotiTaskQueue:
        with self.__lock:
            if self.__is_shutdown:
                logging.error(f"fail on create task queue {options.queue}. PyNotiCenter is shutdown.")
                raise ValueError("PyNotiCenter is shutdown, can not create task queue.")

        if options.queue is None:
            queue = PyNotiTaskQueue(options.queue, self.__scheduler_runloop, self.__common_thread_pool)
            queue.set_fn_with_task_id(options.fn_with_task_id)
            with self.__lock:
                self.__unnamed_task_queue.append(queue)
                self.__unnamed_task_queue = [queue for queue in self.__unnamed_task_queue if not queue.is_terminated]
            return queue

        with self.__lock:
            if options.queue in self.__task_queue_dict:
                return self.__task_queue_dict[options.queue]

        queue = PyNotiTaskQueue(options.queue, self.__scheduler_runloop, self.__common_thread_pool)
        queue.set_fn_with_task_id(options.fn_with_task_id)
        with self.__lock:
            self.__task_queue_dict[options.queue] = queue
        return queue

    def get_default_task_queue(self) -> PyNotiTaskQueue:
        with self.__lock:
            return self.__default_queue

    def get_task_queue(self, queue_name: str) -> PyNotiTaskQueue:
        if queue_name is None:
            return self.__default_queue

        with self.__lock:
            if queue_name not in self.__task_queue_dict:
                raise ValueError("task queue not exist.")

            return self.__task_queue_dict[queue_name]

    def __scheduler_thread__(self):
        logging.info(f"scheduler thread begin.")
        asyncio.set_event_loop(self.__scheduler_runloop)
        loop = self.__scheduler_runloop
        try:
            loop.run_forever()
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            logging.info("scheduler thread end.")

    def add_observer(
        self,
        name: str,
        fn: Callable[..., Any],
        receiver: Optional[Any] = None,
        *,
        options: Optional[PyNotiOptions] = None,
    ):
        with self.__lock:
            observer_collection: Optional[PyNotiObserverCollection] = None
            if name in self.__notifications_dict:
                observer_collection = self.__notifications_dict[name]

            if observer_collection is None:
                observer_collection = PyNotiObserverCollection(name, self.__notification_scheduler__)

            observer_collection.add_observer(fn, receiver, options=options)
            self.__notifications_dict[name] = observer_collection

    def remove_observer(self, name: str, fn: Callable[..., Any], receiver: Any = None):
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
        observer_collection = self.__get_notification_observer_collection__(name)
        if observer_collection is not None:
            observer_collection.notify_observers(*args, **kwargs)

    def __get_notification_observer_collection__(self, name: str) -> PyNotiObserverCollection:
        with self.__lock:
            if name not in self.__notifications_dict:
                raise ValueError(f"observer collection name not exist. {name}")
            return self.__notifications_dict[name]

    def __notification_scheduler__(self, observer: PyNotiObserver, *args: Any, **kwargs: Any):
        if observer.options is None:
            self.post_task(observer.fn, *args, **kwargs)
            return
        # switch to target task queue
        self.post_task_to_task_queue(observer.options.queue, observer.fn, *args, **kwargs)
