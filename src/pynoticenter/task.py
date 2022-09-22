import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from inspect import iscoroutine
from typing import Any, Awaitable, Callable, Coroutine


class PyNotiTask(object):
    __task_id: str = ""
    __preprocessor: callable = None
    __delay: float = 0
    __fn: callable = None
    __is_async: bool = False
    __args: Any = None
    __kwargs: dict[str, Any] = None
    __timer_handle: asyncio.TimerHandle = None

    def __init__(
        self,
        task_id: str,
        delay: float,
        fn: callable,
        preprocessor: callable,
        *args: Any,
        **kwargs: Any,
    ):
        self.__task_id = task_id
        self.__preprocessor = preprocessor
        self.__delay = delay
        self.__fn = fn
        self.__args = args
        self.__kwargs = kwargs
        self.__is_async = False

    @property
    def task_id(self) -> str:
        return self.__task_id

    @property
    def is_async(self) -> bool:
        return self.__is_async

    @is_async.setter
    def is_async(self, is_async: bool):
        self.__is_async = is_async

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
                self.__fn(*self.__args, **self.__kwargs)
        except Exception as e:
            logging.error(e)

    async def async_execute(self):
        if self.__fn is None:
            return
        logging.debug(f"Task[{self.__task_id}] execute.")
        try:
            handled = False
            if self.__preprocessor is not None:
                handled = self.__preprocessor(self.__fn, *self.__args, **self.__kwargs)
            if not handled:
                await self.__fn(*self.__args, **self.__kwargs)
        except Exception as e:
            logging.error(e)
