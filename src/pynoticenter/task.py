import asyncio
import logging
from typing import Any


class PyNotiTask(object):
    __task_id: str = ""
    __preprocessor: callable = None
    __delay: int = 0
    __fn: callable = None
    __args: Any = None
    __kwargs: dict[str, Any] = None
    __timer_handle: asyncio.TimerHandle = None

    def __init__(
        self,
        task_id: str,
        delay: int,
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

    @property
    def delay(self) -> int:
        return self.__delay

    def set_delay(self, delay: int):
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
