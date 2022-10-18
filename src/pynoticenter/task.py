import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional


class PyNotiTask:
    def __init__(
        self,
        task_id: str,
        delay: float,
        fn: Optional[Callable[..., Any]],
        preprocessor: Optional[Callable[..., Any]],
        *args: Any,
        executor: Optional[ThreadPoolExecutor],
        **kwargs: Any,
    ):
        self.__task_id: str = task_id
        self.__preprocessor: Optional[Callable[..., Any]] = preprocessor
        self.__delay: float = delay
        self.__fn: Optional[Callable[..., Any]] = fn
        self.__args: Any = args
        self.__kwargs: Dict[str, Any] = kwargs
        self.__timer_handle: Optional[asyncio.TimerHandle] = None
        self.__thread_pool: Optional[ThreadPoolExecutor] = executor
        self.__fn_with_task_id: bool = False

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
        return self.__timer_handle.cancelled()

    def set_timer_handle(self, handle: asyncio.TimerHandle):
        self.__timer_handle = handle

    def cancel(self):
        if self.__timer_handle is None:
            return
        if self.__timer_handle.cancelled():
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
                    if self.__fn_with_task_id:
                        handled = await self.__preprocessor(self.__fn, *self.__task_id, *self.__args, **self.__kwargs)
                    else:
                        handled = await self.__preprocessor(self.__fn, *self.__args, **self.__kwargs)
                else:
                    if self.__fn_with_task_id:
                        handled = self.__preprocessor(self.__fn, *self.__task_id, *self.__args, **self.__kwargs)
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
