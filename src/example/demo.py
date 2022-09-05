import logging
import sys
import time
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


def mytask2_fn():
    print("mytask2 fn")


def mytask_preprocessor(fn: callable, *args: Any, **kwargs: Any) -> bool:
    print("mytask preprocessor")
    # IF YOU SCHEDULE NEW TASK AFTER YOU SHUTDOWN THE PYNOTICENTER, IT WILL BE IGNORED.
    # PyNotiCenter.default().post_task_to_task_queue("mytask2", mytask2_fn)
    return False


def main():
    queue = PyNotiCenter.default().create_task_queue("mytask")
    queue.set_preprocessor(mytask_preprocessor)

    a = A()
    PyNotiCenter.default().add_observer("say_hello", say_hello)
    PyNotiCenter.default().add_observer("say_hello", a.say_hi, a)
    PyNotiCenter.default().add_observer("say_hello", a.say_hi, a, options=PyNotiOptions(queue="mytask"))

    PyNotiCenter.default().notify_observers("say_hello", "lily")

    PyNotiCenter.default().shutdown(wait=True)


if __name__ == "__main__":
    main()
