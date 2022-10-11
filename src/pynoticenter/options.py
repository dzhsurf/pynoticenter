from dataclasses import dataclass


@dataclass(frozen=True)
class PyNotiOptions:
    queue: str
    fn_with_task_id: bool = False
