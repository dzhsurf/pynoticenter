from dataclasses import dataclass


@dataclass(frozen=True)
class PyNotiOptions:
    queue: str
