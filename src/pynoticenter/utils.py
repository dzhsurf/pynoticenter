import logging
import threading
from typing import Any


def __thread_fn__(event: threading.Event, fn: callable, *args: Any, **kwargs: Any):
    pass


def RunInThread(fn: callable, *args: Any, **kwargs: Any) -> threading.Event:
    event = threading.Event()

    def thread_fn():
        if fn is not None:
            try:
                fn(*args, **kwargs)
            except Exception as e:
                logging.error(e)
        event.set()

    t = threading.Thread(target=thread_fn)
    t.start()
    return event


def Wait(event: threading.Event):
    timeout = 5.0
    while not event.is_set():
        event.wait(timeout)
