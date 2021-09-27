from __future__ import annotations
from typing import Callable, NamedTuple


class APIRecord(NamedTuple):
    method: str
    url: str
    callback: Callable[[], None]
