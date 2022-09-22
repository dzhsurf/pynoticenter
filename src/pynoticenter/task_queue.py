import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Any, final

from pynoticenter import utils
from pynoticenter.task import PyNotiTask

PYNOTI_INTERVAL = 0.5


class PyNotiTaskQueue(object):
    """PyNotiTaskQueue, each task queue has its own thread. All function thread safety"""

    __name: str = ""
    __lock: threading.RLock = None
    __is_terminated: bool = False
    __wait_until_task_done: bool = True
    __is_started: bool = False
    __task_id_count: int = 0
    __task_dict: dict[str, PyNotiTask] = None
    __tasks_counter_signal: threading.Event = None
    __preprocessor: callable = None
    __execute_runloop: asyncio.AbstractEventLoop = None
    __execute_task_thread: threading.Thread = None
    __execute_thread_event: threading.Event = None
    __scheduler_runloop: asyncio.AbstractEventLoop = None
    __pending_tasks: Queue[PyNotiTask] = None
    __thread_pool: ThreadPoolExecutor = None

    def __init__(self, name: str, scheduler_runloop: asyncio.AbstractEventLoop, thread_pool: ThreadPoolExecutor):
        self.__name = name if name is not None else f"{id(self)}"
        self.__lock = threading.RLock()
        self.__task_dict = dict()
        self.__tasks_counter_signal = threading.Event()
        self.__pending_tasks = Queue()
        self.__preprocessor = None
        self.__thread_pool = thread_pool
        self.__scheduler_runloop = scheduler_runloop
        self.__execute_runloop = asyncio.new_event_loop()
        self.__execute_thread_event = threading.Event()
        self.__execute_task_thread = threading.Thread(target=self.__worker_thread__)

    @property
    def is_terminated(self) -> bool:
        with self.__lock:
            return self.__is_terminated

    @property
    def task_count(self) -> int:
        with self.__lock:
            return len(self.__task_dict)

    def __terminate_thread_callback__(self, wait: bool):
        # run in thread.
        with self.__lock:
            if self.__is_terminated:
                return

        with self.__lock:
            self.__is_terminated = True
            self.__wait_until_task_done = wait
        if not wait:
            self.__scheduler_runloop.call_soon_threadsafe(self.__cancel_scheduled_task__)
        self.__wait_until_tasks_cleanup__()

        # stop run loop and wait for thread exit.
        self.__execute_runloop.call_soon_threadsafe(self.__cleannup_thread__)
        self.__wait_until_thread_exit__()

    def terminate(self, wait: bool = True):
        # terminate thread and stop event loop
        logging.info(f"{self.__log_prefix__()}: Task queue terminate. wait: {wait}")
        event = utils.RunInThread(self.__terminate_thread_callback__, wait, executor=self.__thread_pool)
        if wait:
            utils.Wait(event)

    def set_preprocessor(self, preprocessor: callable):
        with self.__lock:
            self.__preprocessor = preprocessor

    def post_task(self, fn: callable, *args: Any, **kwargs: Any) -> str:
        return self.post_task_with_delay(0, fn, *args, **kwargs)

    def post_task_with_delay(self, delay: float, fn: callable, *args: Any, **kwargs: Any) -> str:
        task_id = ""
        with self.__lock:
            if self.is_terminated:
                logging.info(f"{self.__log_prefix__():}: task queue is terminated. ignore new task.")
                return

            # add task
            task_id = str(self.__task_id_count + 1)
            self.__task_id_count += 1
            task = PyNotiTask(task_id, delay, fn, self.__preprocessor, *args, executor=self.__thread_pool, **kwargs)
            self.__task_dict[task_id] = task
            self.__scheduler_runloop.call_soon_threadsafe(self.__tasks_update_callback__)

            # start thread
            if not self.__is_started:
                self.__is_started = True
                self.__execute_task_thread.start()

            # dispatch task
            self.__scheduler_runloop.call_soon_threadsafe(self.__schedule_task__, task_id)

        return task_id

    def cancel_task(self, task_id: str):
        logging.info(f"{self.__log_prefix__()}: cancel task {task_id}")
        task: PyNotiTask = None
        with self.__lock:
            task = self.__pop_task__(task_id)
        if task is not None:
            self.__scheduler_runloop.call_soon_threadsafe(task.cancel)

    def __pop_task__(self, task_id: str) -> PyNotiTask:
        with self.__lock:
            if task_id in self.__task_dict:
                task = self.__task_dict.pop(task_id)
                self.__scheduler_runloop.call_soon_threadsafe(self.__tasks_update_callback__)
                return task
        return None

    def __tasks_update_callback__(self):
        # call from scheduler thread
        with self.__lock:
            if self.is_terminated and self.task_count == 0:
                self.__tasks_counter_signal.set()

    def __log_prefix__(self):
        return f"TaskQueue[{self.__name}]"

    def __wait_until_tasks_cleanup__(self):
        # wait for all task finish
        task_count = self.task_count
        logging.info(f"{self.__log_prefix__()}: waiting for tasks cleanup. tasks: {task_count}")
        begin_time = time.time()
        if task_count == 0:
            logging.info(f"{self.__log_prefix__()}: All tasks cleanup.")
            return

        while not self.__tasks_counter_signal.is_set():
            self.__tasks_counter_signal.wait(PYNOTI_INTERVAL)
            wait_time = time.time() - begin_time
            logging.debug(
                f"{self.__log_prefix__()}: waiting for tasks finish. time: {wait_time:0.3f} tasks: {self.task_count}"
            )
        wait_time = time.time() - begin_time
        logging.info(f"{self.__log_prefix__()}: All tasks cleanup. wait time: {wait_time:0.3f}")

    def __wait_until_thread_exit__(self):
        logging.info(f"{self.__log_prefix__()}: waiting for thread exit.")
        begin_time = time.time()
        with self.__lock:
            if self.__execute_task_thread is None or not self.__is_started:
                self.__execute_thread_event.set()
        while not self.__execute_thread_event.is_set():
            self.__execute_thread_event.wait(PYNOTI_INTERVAL)
            wait_time = time.time() - begin_time
            logging.debug(f"{self.__log_prefix__()}: waiting for thread exit. time: {wait_time:0.3f}")
        wait_time = time.time() - begin_time
        logging.info(f"{self.__log_prefix__()}: thread exit. wait time: {wait_time:0.3f}")

    def __cancel_scheduled_task__(self):
        logging.info(f"{self.__log_prefix__()}: cancel scheduled task.")
        with self.__lock:
            task_ids = list()
            task_ids.extend(self.__task_dict.keys())
            for task_id in task_ids:
                self.cancel_task(task_id)

    def __cleannup_thread__(self):
        logging.info(f"{self.__log_prefix__()}: stop event run loop.")
        with self.__lock:
            self.__execute_runloop.stop()

    def __schedule_task__(self, task_id: str):
        # call from scheduler thread, asyncio event loop.
        need_execute = False
        delay = 0
        task: PyNotiTask = None
        with self.__lock:
            # check task exist or not
            if task_id in self.__task_dict:
                task = self.__task_dict[task_id]
            if task is None:
                self.__pop_task__(task_id)
                return

            # if task queue is terminated, remove task.
            if self.is_terminated and not self.__wait_until_task_done:
                task.cancel()
                self.__pop_task__(task_id)
                return

            # if task have delay, reschedule task. otherwise, add task to pending list.
            if task.delay == 0:
                need_execute = True
            else:
                delay = task.delay
                handler = self.__scheduler_runloop.call_later(delay, self.__schedule_task__, task_id)
                task.set_delay(0)
                task.set_timer_handle(handler)

        if need_execute:
            # add to pending list, waiting for execution.
            with self.__lock:
                self.__pending_tasks.put(task)
            self.__execute_runloop.call_soon_threadsafe(self.__check_and_execute_tasks__)

    def __check_and_execute_tasks__(self):
        # call from worker thread
        task: PyNotiTask = None
        while True:
            with self.__lock:
                if self.__pending_tasks.empty():
                    break
                task = self.__pending_tasks.get()
                if task is not None and task.task_id not in self.__task_dict:
                    task.cancel()
                    task = None
            if task is None:
                continue

            task.execute()
            self.__pop_task__(task.task_id)

    def __worker_thread__(self):
        logging.info(f"{self.__log_prefix__()}: worker thread begin.")
        loop = self.__execute_runloop
        asyncio.set_event_loop(self.__execute_runloop)
        with self.__lock:
            if self.__is_terminated and not self.__wait_until_task_done:
                # terminate before the thread start. cancel the schedule task again
                self.__scheduler_runloop.call_soon_threadsafe(self.__cancel_scheduled_task__)

        try:
            loop.run_forever()
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            logging.info(f"{self.__log_prefix__()}: worker thread end.")
            with self.__lock:
                self.__execute_task_thread = None
            self.__execute_thread_event.set()
