import asyncio
import logging
import sys
import threading
import time
from select import select
from typing import Any

from pynoticenter.noticenter import PyNotiCenter
from pynoticenter.options import PyNotiOptions

# setup logger
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [stdout_handler]
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    handlers=handlers,
)
logger = logging.getLogger(__name__)

# demo


def say_hello(who: str):
    print(f"{who}: hello")


class A:
    def say_hi(self, who: str):
        print(f"A.say_hi, {who}: hi")

    def say_bye(self, who: str):
        print(f"A.say_bye, {who}: bye")


def fn(msg: str, wait: float = 0.0):
    tid = threading.current_thread().ident
    print(f"fn: {msg}, start in thread,", tid)
    if wait > 0:
        time.sleep(wait)
    print(f"fn: {msg} end, wait {wait}s")


async def async_fn(msg: str, wait: float = 0.0):
    tid = threading.current_thread().ident
    print(f"async fn: {msg} start in thread", tid)
    if wait > 0:
        await asyncio.sleep(wait)
    print(f"async fn: {msg} end, wait {wait}s")


def mytask_preprocessor(fn: callable, *args: Any, **kwargs: Any) -> bool:
    print("mytask preprocessor")
    # IF YOU SCHEDULE NEW TASK AFTER YOU SHUTDOWN THE PYNOTICENTER, IT WILL BE IGNORED.
    # PyNotiCenter.default().post_task_to_task_queue("mytask2", mytask2_fn)
    return False


def main():
    queue = PyNotiCenter.default().create_task_queue("mytask")
    queue.set_preprocessor(mytask_preprocessor)
    queue.post_task(fn, "1")
    queue.post_task(async_fn, "2", 5)
    queue.post_task(fn, "3", 1)
    task_id = queue.post_task_with_delay(5.0, fn, "6")
    queue.post_task(fn, "4", 5)
    queue.post_task_with_delay(1.0, async_fn, "5")
    # queue.cancel_task(task_id)
    PyNotiCenter.default().post_task(fn, "d_1")
    PyNotiCenter.default().post_task(async_fn, "d_2", 1)

    # a = A()
    # PyNotiCenter.default().add_observer("say_hello", say_hello)
    # PyNotiCenter.default().add_observer("say_hello", a.say_hi, a)
    # PyNotiCenter.default().add_observer("say_hello", a.say_hi, a, options=PyNotiOptions(queue="mytask"))

    # PyNotiCenter.default().notify_observers("say_hello", "lily")

    PyNotiCenter.default().shutdown(wait=True)


if __name__ == "__main__":
    main()
