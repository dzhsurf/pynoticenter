Quickstart
==========

[![Docs](https://img.shields.io/badge/docs-latest-informational)](https://dzhsurf.github.io/pynoticenter/)

PyPI: [https://pypi.org/project/pynoticenter/](https://pypi.org/project/pynoticenter/)

Introduction
------------

PyNotiCenter is a multithreaded task queue and message notification center. It mainly provides in-process lightweight task scheduling management for client applications, that why we choose the multi-threaded mode. Although the multi-threaded mode is not a good practice most of the time in Python(In CPU-bound tasks it can't be genuinely parallel as the GIL exists). But in developing client applications, it will be one of the most important base components.

As it is based on a multi-threaded mode, multi-threaded development must pay attention to thread safety issues, which is inevitable. In order to reduce the complexity for developers, all interfaces of this library are thread safety. It is designed to be called in any thread to guarantee the same results as expected, even though this will cause some performance issues.

The library mainly provides 2 features.

* Task queue: each task queue will run in a separate thread.
* Message notification: the message notification scheduling is based on the built-in task queue.

Install
-------

```shell
pip install pynoticenter
```

Code Example
------------

* Post task to task queue.

```python
def fn(*args: Any, **kwargs: Any):
    print(*args)

def main():
    PyNotiCenter.default().post_task(fn, "hello world")
    PyNotiCenter.default().post_task_with_delay(5, False, fn, "hello", "world", "delay 5s")
    PyNotiCenter.default().shutdown(wait=True)
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

```python
# async func
async def async_fn(msg: str):
  await asyncio.sleep(1)
  print(f"msg: {msg}")

def fn(msg: str):
  print(f"msg: {msg}")

def main():
  PyNotiCenter.default().post_task(fn, "hello")
  PyNotiCenter.default().post_task(async_fn, "hello")
  PyNotiCenter.default().wait_until_task_complete()
  PyNotiCenter.default().shutdown(wait=True)
```

* Notification

```python
class A:
    def say_hello(self, who: str):
        print(f"{who}: hello")

def main():
    receiver = A()
    PyNotiCenter.default().add_observer("say_hello", receiver.say_hello, receiver)
    PyNotiCenter.default().notify_observers("say_hello", "baby")
    ...
    PyNotiCenter.default().remove_observers(receiver)
    PyNotiCenter.default().shutdown(wait=True)
```

* Notification on specific thread, such as Gtk main thread.

```python
def fn():
    pass

def switch_to_gtk_thread(fn: Callable, *args: Any, **kwargs) -> bool:
    GLib.idle_add(fn)
    return True

def main():
    queue = PyNotiCenter.default().create_task_queue(PyNotiOptions(queue='mytask'))
    queue.set_preprocessor(switch_to_gtk_thread)
    queue.post_task(fn) # fn run in gtk thread

    # notification run on mytask queue.
    PyNotiCenter.default().add_observer("say_hello", fn, options=PyNotiOptions(queue="mytask"))
    PyNotiCenter.default().notify_observers("say_hello")
```

Post task with task id

```python
def fn_with_task_id(task_id: str, msg: str):
    pass

def main():
    queue = PyNotiCenter.default().create_task_queue(PyNotiOptions(queue='mytask', fn_with_task_id=True))
    task_id = queue.post_task(fn_with_task_id, 'Hi')
    queue.cancel_task(task_id)
```
