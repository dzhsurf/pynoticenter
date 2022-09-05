import logging
import sys
import time
from typing import Any

from pynoticenter.noticenter import PyNotiCenter

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


def main():
    a = A()
    PyNotiCenter.default().add_observer("say_hello", say_hello)
    PyNotiCenter.default().add_observer("say_hello", a.say_hi, a)
    PyNotiCenter.default().add_observer("say_hi", a.say_hi, a)
    PyNotiCenter.default().add_observer("say_bye", a.say_bye, a)

    PyNotiCenter.default().notify_observers("say_hello", "Terry")
    PyNotiCenter.default().notify_observers("say_hi", "Terry")
    time.sleep(1)

    PyNotiCenter.default().remove_observer("say_hello", say_hello)
    PyNotiCenter.default().notify_observers("say_hello", "Tommy")
    time.sleep(1)

    PyNotiCenter.default().remove_observer("say_bye", a.say_bye, a)
    PyNotiCenter.default().notify_observers("say_bye", "Terry")
    time.sleep(1)

    PyNotiCenter.default().remove_observers(a)
    PyNotiCenter.default().notify_observers("say_hello", "Andy")

    PyNotiCenter.default().shutdown(wait=True)


if __name__ == "__main__":
    main()
