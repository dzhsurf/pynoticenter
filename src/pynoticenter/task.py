import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from inspect import iscoroutine, iscoroutinefunction
from typing import Any, Awaitable, Callable, Coroutine


class PyNotiTask(object):
    __task_id: str = ""
    __preprocessor: callable = None
    __delay: float = 0
    __fn: callable = None
    __args: Any = None
    __kwargs: dict[str, Any] = None
    __timer_handle: asyncio.TimerHandle = None
    __thread_pool: ThreadPoolExecutor = None

    def __init__(
        self,
        task_id: str,
        delay: float,
        fn: callable,
        preprocessor: callable,
        *args: Any,
        executor: ThreadPoolExecutor,
        **kwargs: Any,
    ):
        self.__task_id = task_id
        self.__preprocessor = preprocessor
        self.__delay = delay
        self.__fn = fn
        self.__args = args
        self.__kwargs = kwargs
        self.__thread_pool = executor

    @property
    def task_id(self) -> str:
        return self.__task_id

    @property
    def delay(self) -> float:
        return self.__delay

    def set_delay(self, delay: float):
        self.__delay = delay

    @property
    def is_cancelled(self) -> bool:
        if self.__timer_handle is None:
            return False
        return self.__timer_handle.cancelled

    def set_timer_handle(self, handle: asyncio.TimerHandle):
        self.__timer_handle = handle

    def cancel(self):
        if self.__timer_handle is None:
            return
        if self.__timer_handle.cancelled:
            logging.debug(f"Task[{self.__task_id}] has been cancelled.")
            return
        logging.debug(f"Task[{self.__task_id}] cancel task.")
        self.__timer_handle.cancel()

    def execute(self):
        if self.__fn is None:
            return
        logging.debug(f"Task[{self.__task_id}] execute.")
        try:
            handled = False
            if self.__preprocessor is not None:
                handled = self.__preprocessor(self.__fn, *self.__args, **self.__kwargs)
            if not handled:
                if asyncio.iscoroutinefunction(self.__fn):
                    event = threading.Event()

                    def wrap_async_func():
                        try:
                            asyncio.run(self.__fn(*self.__args, **self.__kwargs))
                        finally:
                            event.set()

                    self.__thread_pool.submit(wrap_async_func)
                    event.wait()
                else:
                    self.__fn(*self.__args, **self.__kwargs)
        except Exception as e:
            logging.error(e)
