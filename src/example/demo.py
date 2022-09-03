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
    desc = ""
    for v in args:
        desc += v
    if desc != "":
        desc += " "
    desc += "kwargs: "
    for k, v in kwargs.items():
        desc += f"{k} = {v}"
    print(desc)


def main():
    print("demo start.")
    PyNotiCenter.default_center().post_task(
        fn,
        "fn1",
        desc="post task",
    )
    PyNotiCenter.default_center().post_task_to_task_queue(
        "background_thread",
        fn,
        "fn1",
        desc="post task",
    )
    PyNotiCenter.default_center().post_task_with_delay(
        3,
        fn,
        "fn2",
        desc="post task with delay 3",
    )
    PyNotiCenter.default_center().post_task_with_delay(
        10,
        fn,
        "fn3",
        value="post task with delay 10",
    )
    task_id = PyNotiCenter.default_center().post_task_with_delay(
        4,
        fn,
        "fn3",
        value="post task with delay 4",
    )
    PyNotiCenter.default_center().post_task(
        fn,
        "fn4",
        value="post task",
    )
    #time.sleep(0.3)
    PyNotiCenter.default_center().release_task_queue("background_thread", True)
    PyNotiCenter.default_center().cancel_task(task_id)
    PyNotiCenter.default_center().shutdown(wait=True)
    print("demo end.")


if __name__ == "__main__":
    main()
