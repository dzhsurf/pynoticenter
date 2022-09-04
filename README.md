PyNotiCenter Documentation
==========================

[![Docs](https://img.shields.io/badge/docs-latest-informational)](https://dzhsurf.github.io/pynoticenter/)

## Introduction

Python client side notification center.

## Install

```shell
pip install pynoticenter
```

## Code Example

```python
def fn(*args: Any, **kwargs: Any):
    print(*args)

def main():
    PyNotiCenter.default_center().post_task(fn, "hello world")
    PyNotiCenter.default_center().post_task_with_delay(5, fn, "hello", "world", "delay 5s")
    PyNotiCenter.default_center().shutdown(wait=True)
```

```shell
[2022-09-03 20:54:23,698] {task_queue.py:177} INFO - TaskQueue[4408264928]: worker thread begin.
[2022-09-03 20:54:23,699] {task_queue.py:46} INFO - TaskQueue[4408264928]: Task queue terminate. wait: True
[2022-09-03 20:54:23,699] {task_queue.py:105} INFO - TaskQueue[4408264928]: waiting for tasks cleanup. tasks: 2
hello world
hello world delay 5s
[2022-09-03 20:54:28,721] {task_queue.py:114} INFO - TaskQueue[4408264928]: All tasks cleanup. wait time: 5.0
[2022-09-03 20:54:28,722] {task_queue.py:117} INFO - TaskQueue[4408264928]: waiting for thread exit.
[2022-09-03 20:54:28,722] {task_queue.py:137} INFO - TaskQueue[4408264928]: stop event run loop.
[2022-09-03 20:54:28,723] {task_queue.py:200} INFO - TaskQueue[4408264928]: worker thread end.
[2022-09-03 20:54:29,726] {task_queue.py:126} INFO - TaskQueue[4408264928]: thread exit. wait time: 1.0
```