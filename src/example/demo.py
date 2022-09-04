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


def main():
    PyNotiCenter.default_center().post_task(fn, "hello world")
    PyNotiCenter.default_center().post_task_with_delay(5, fn, "hello", "world", "delay 5s")
    PyNotiCenter.default_center().shutdown(wait=False)
    print("main end")


if __name__ == "__main__":
    main()
