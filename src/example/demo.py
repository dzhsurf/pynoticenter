import asyncio
import logging
import sys
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


def fn(*args: Any, **kwargs: Any):
    print(*args)


def say_hello(who: str):
    print(f"{who}: hello")


class A:
    def say_hi(self, who: str):
        print(f"A.say_hi, {who}: hi")

    def say_bye(self, who: str):
        print(f"A.say_bye, {who}: bye")


async def async_fn():
    print("async_fn")
    await asyncio.sleep(1)
    time.sleep(1)
    print("async_fn finish")


async def mytask2_fn():
    print("mytask2 fn")
    # await task here
    task = asyncio.ensure_future(async_fn())
    await task
    print("mytask2 fn end")


def mytask_preprocessor(fn: callable, *args: Any, **kwargs: Any) -> bool:
    print("mytask preprocessor")
    # IF YOU SCHEDULE NEW TASK AFTER YOU SHUTDOWN THE PYNOTICENTER, IT WILL BE IGNORED.
    # PyNotiCenter.default().post_task_to_task_queue("mytask2", mytask2_fn)
    return False


def fn_wait():
    print("fn_wait 5s begin")
    time.sleep(5)
    print("fn_wait 5s finish")


def main():
    queue = PyNotiCenter.default().create_task_queue("mytask")
    queue.set_preprocessor(mytask_preprocessor)
    queue.post_task(fn, "fn")
    queue.post_async_task(mytask2_fn)
    queue.post_task(fn, "fn again")
    task_id = queue.post_task_with_delay(5.0, False, fn_wait)
    queue.post_task(fn, "fn again 3")
    PyNotiCenter.default().post_task(fn, "hello")
    PyNotiCenter.default().post_async_task(mytask2_fn)
    # queue.cancel_task(task_id)

    # a = A()
    # PyNotiCenter.default().add_observer("say_hello", say_hello)
    # PyNotiCenter.default().add_observer("say_hello", a.say_hi, a)
    # PyNotiCenter.default().add_observer("say_hello", a.say_hi, a, options=PyNotiOptions(queue="mytask"))

    # PyNotiCenter.default().notify_observers("say_hello", "lily")

    PyNotiCenter.default().shutdown(wait=True)


if __name__ == "__main__":
    main()
