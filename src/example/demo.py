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
        desc += v + ", "
    if desc != "":
        desc += " "
    desc += "kwargs: "
    for k, v in kwargs.items():
        desc += f"{k} = {v}, "
    print(desc)


def main():

    print("demo start.")
    for i in range(100000):
        PyNotiCenter.default_center().post_task(fn, f"hello {i}", key="k", value="v")
    time.sleep(0.5)
    PyNotiCenter.default_center().shutdown(wait=False)
    print("demo end.")


if __name__ == "__main__":
    main()
