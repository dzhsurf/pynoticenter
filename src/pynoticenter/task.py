import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from inspect import iscoroutine, iscoroutinefunction
from typing import Any, Awaitable, Callable, Coroutine, Dict


class PyNotiTask(object):
    __task_id: str = ""
    __preprocessor: Callable = None
    __delay: float = 0
    __fn: Callable = None
    __args: Any = None
    __kwargs: Dict[str, Any] = None
    __timer_handle: asyncio.TimerHandle = None
    __thread_pool: ThreadPoolExecutor = None
    __fn_with_task_id: bool = False

    def __init__(
        self,
        task_id: str,
        delay: float,
        fn: Callable,
        preprocessor: Callable,
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

    def set_with_task_id(self, with_task_id: bool):
        self.__fn_with_task_id = with_task_id

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

    def is_async(self):
        return asyncio.iscoroutinefunction(self.__fn)

    async def execute(self):
        if self.__fn is None:
            return
        logging.debug(f"Task[{self.__task_id}] execute.")
        try:
            handled = False
            if self.__preprocessor is not None:
                if asyncio.iscoroutinefunction(self.__preprocessor):
                    handled = await self.__preprocessor(self.__fn, *self.__args, **self.__kwargs)
                else:
                    handled = self.__preprocessor(self.__fn, *self.__args, **self.__kwargs)
            if not handled:
                if asyncio.iscoroutinefunction(self.__fn):
                    if self.__fn_with_task_id:
                        await self.__fn(self.__task_id, *self.__args, **self.__kwargs)
                    else:
                        await self.__fn(*self.__args, **self.__kwargs)
                else:
                    if self.__fn_with_task_id:
                        self.__fn(self.__task_id, *self.__args, **self.__kwargs)
                    else:
                        self.__fn(*self.__args, **self.__kwargs)
        except Exception as e:
            logging.error(e)
